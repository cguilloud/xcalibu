#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# xcalibu.py
# Calibration Manager
#
# Xcalibu is a class to deal with calibrations.
#
# A calibration is :
# * read from a file
# * defined by a string
# * created from numpy arrays
# it stores information as a table or as a polynom.
#
#  example of field of a table in a file : U32BC1G[5.00]=14.05
#
# The Xcalibu class mainly provides the following method :
#   get_y(x) which returns the f(x) fitted value.
#
# If using TABLE, the class performs the fit of the raw data and
# furnishes a y=f(x) polynomial function.
#
# The returned value is calculated by various reconstruction methods
# depending on the calibration type and parameters.
#   TABLE ----> INTERPOLATION   |  POLYFIT
#   POLY  ----> Direct calculation
#
# The reverse function "get_x(y)" is also available.
# Take care : get_x(get_y(x)) can be different from x due to
# approximation of fitting.
# get_x is usable only for poly and fitted tables
#
# Intrinsec parameters of a calibration (parameters fixed at calib
# recording/generation):
# * CALIB_NAME
# * CALIB_TYPE
# * CALIB_TIME
# * CALIB_DESC
#
# and 3 more for polynoms (min and max are automatically calculated for TABLES):
# * CALIB_XMIN
# * CALIB_XMAX
# * CALIB_ORDER
#
# Usage parameters (parameters that a user can change to use its
# calibration):
# * RECONSTRUCTION_METHOD : POLYFIT or INTERPOLATION
# * FIT_ORDER (for a TABLE calib and POLYFIT reconstruction_method)


# TODO: drop usage of old format ?


import os
import logging
import numbers
import numpy
import re
import sys
import time

from operator import itemgetter

try:
    import timedisplay

    TIME_DISPLAY_FOUND = True
except ImportError:
    TIME_DISPLAY_FOUND = False

log = logging.getLogger("XCALIBU")
LOG_FORMAT = "%(name)s - %(levelname)s - %(message)s"

XCALIBU_DIRBASE = os.path.dirname(os.path.realpath(__file__))

__all__ = ["Xcalibu", "XCalibError"]


class XCalibError(Exception):
    """Custom exception class for Xcalibu."""

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return "XCALIBU error: %s" % self.message


class Xcalibu:
    def __init__(
        self,
        calib_string=None,
        calib_file_name=None,
        fit_order=None,
        reconstruction_method=None,
    ):
        self._calib_string = None
        self._calib_file_name = None
        self._calib_file_format = "SIMPLE"
        self._fit_order = 0
        self._rec_method = None

        self._calib_name = None
        self._calib_type = "TABLE"
        self._calib_time = None
        self._description = None
        self._calib_order = 0
        self._file_name = None

        self.Xmin = 0.0
        self.Xmax = 0.0
        self.Ymin = 0.0
        self.Ymax = 0.0

        self._data_lines = 0
        self._comments = []

        """
        Parameters recording
        """
        # Calib string.
        if calib_string is not None:
            self.set_calib_string(calib_string)

        # Calib file name.
        if calib_file_name is not None:
            self.set_calib_file_name(calib_file_name)

        # Poly order to be used by reconstruction method for TABLE calibrations.
        if fit_order is not None:
            self._fit_order = fit_order

        # Reconstruction method for TABLE calibrations:
        # * INTERPOLATION : interpolation segment by segment.
        # * POLYFIT : polynomial fitting of the dataset.
        if reconstruction_method is not None:
            self.set_reconstruction_method(reconstruction_method)

        # Load !
        if (
            self.get_calib_file_name() is not None
            or self.get_calib_string() is not None
        ):
            # A calib string or a file name is defined, try to load the calib.
            self.load_calib()

    def set_calib_file_name(self, fn):
        """
        Set name of the file to use to load/save a calibration.
        """
        log.debug("set_calib_file_name(%s)" % fn)
        self._calib_file_name = fn

    def get_calib_file_name(self):
        return self._calib_file_name

    def set_calib_string(self, calib_string):
        """
        Set string to use to create a calibration.
        """
        self._calib_string = calib_string

    def get_calib_string(self):
        return self._calib_string

    def set_calib_name(self, value):
        """
        Calibration name is read from the calibration file or string (field : CALIB_NAME).
        """
        self._calib_name = value

    def get_calib_name(self):
        """
        Calibration name is read from the calibration file or string (field : CALIB_NAME).
        """
        return self._calib_name

    def set_calib_type(self, value):
        """
        Sets calibration type read from calibration file or string (field : CALIB_TYPE).
        Can be TABLE or POLY.
        """
        self._calib_type = value

    def get_calib_type(self):
        """
        Return calibration type read from calibration file or string (field : CALIB_TYPE).
        Can be 'TABLE' or 'POLY'.
        """
        return self._calib_type

    """
    'fit order' used to fit TABLE calibrations.
    """

    def set_fit_order(self, order):
        if isinstance(order, int) and order > 0:
            self._fit_order = order
        else:
            log.error("set_fit_order : <fit_order> must be a positive integer.")

    def get_fit_order(self):
        return self._fit_order

    """
    time of creation of the calibration (seconds since epoch)
    """

    def set_calib_time(self, timestamp):
        self._calib_time = timestamp

    def get_calib_time(self):
        return self._calib_time

    """
    Sets order of polynomia used to define calibration (NOT TO FIT).
    Read from POLY calibration file (field : CALIB_ORDER).
    """

    def set_calib_order(self, order):
        if isinstance(order, int) and order > 0:
            self._calib_order = order
        else:
            log.error("set_calib_order : <calib_order> must be a positive integer.")

    def get_calib_order(self):
        return self._calib_order

    """
    calibration description string.
    """

    def set_calib_description(self, value):
        self._description = value

    def get_calib_description(self):
        return self._description

    """
    x raw data numpy array.
    """

    def set_raw_x(self, arr_x):
        self.x_raw = arr_x
        self.Xmin = self.x_raw.min()
        self.Xmax = self.x_raw.max()

        # ??? must update dataset size !!!@!@#!@#$#

    def get_raw_x(self):
        return self.x_raw

    def set_raw_y(self, arr_y):
        """
        Sets y raw data numpy array.
        """
        self.y_raw = arr_y
        self.Ymin = self.y_raw.min()
        self.Ymax = self.y_raw.max()

    def get_raw_y(self):
        return self.y_raw

    """
    calibration USAGE parameters.
    """

    def set_reconstruction_method(self, method):
        """
        Sets method for fitting : can be 'INTERPOLATION' or 'POLYFIT'
        """
        if method in ["INTERPOLATION", "POLYFIT"]:
            self._rec_method = method
        else:
            raise XCalibError("unknown method : %s " % method)

    def get_reconstruction_method(self):
        return self._rec_method

    def load_calib(self):
        """
        Calibration loading :
        * read calib file (Table or Poly)
        * parse header and data
        * fit points if required
        """
        _x_min = float("inf")
        _x_max = -float("inf")
        _y_min = float("inf")
        _y_max = -float("inf")
        _nb_points = 0
        _line_nb = 0
        _data_line_nb = 0
        _header_line_nb = 0
        _part_letter = (
            "H"
        )  # letter to indicate (in debug) the section of the calibration file: H(eader) or D(ata)
        _xvalues = []
        _yvalues = []

        _calib_file_name = self.get_calib_file_name()
        _calib_string = self.get_calib_string()

        if _calib_file_name is not None:
            try:
                calib_source = open(_calib_file_name, mode="r")
            except IOError:
                raise XCalibError("Unable to open file '%s' \n" % _calib_file_name)
            except Exception:
                raise XCalibError(
                    "error in calibration loading (file=%s)" % _calib_file_name
                )
        elif _calib_string is not None:
            # print("loading calib from string:")
            calib_source = _calib_string.split("\n")
        else:
            raise RuntimeError("Unable to load calibration: no string of filename provided.")

        try:
            for raw_line in calib_source:
                _line_nb = _line_nb + 1

                # Remove optional "whitespace" characters :
                # string.whitespace -> '\t\n\x0b\x0c\r '
                line = raw_line.strip()

                # Line is empty or full of space(s).
                if len(line) == 0:
                    log.debug("line %4d%s : empty" % (_line_nb, _part_letter))
                    continue

                # Commented line
                if line[0] == "#":
                    log.debug(
                        "line %4d%s : comment    : {%s}"
                        % (_line_nb, _part_letter, line.rstrip())
                    )
                    self._comments.append(line)
                    continue

                # Matche lines like :
                # CALIB_<info> = <value>
                matchCalibInfo = re.search(r"CALIB_(\w+)(?: )*=(?: )*(.+)", line)
                if matchCalibInfo:
                    _header_line_nb = _header_line_nb + 1
                    _info = matchCalibInfo.group(1)
                    _value = matchCalibInfo.group(2)

                    log.debug(
                        "line %4d%s : calib info : %30s   info={%s} value={%s}"
                        % (
                            _line_nb,
                            _part_letter,
                            matchCalibInfo.group(),
                            _info,
                            _value,
                        )
                    )

                    if _info == "NAME":
                        self.set_calib_name(_value)
                    elif _info == "TYPE":
                        self.set_calib_type(_value)
                    elif _info == "TIME":
                        self.set_calib_time(int(_value.split(".")[0]))
                    elif _info == "ORDER":
                        self.set_calib_order(int(_value))
                        self.coeffs = numpy.linspace(0, 0, self.get_calib_order() + 1)
                    elif _info == "XMIN":
                        self.Xmin = float(_value)
                    elif _info == "XMAX":
                        self.Xmax = float(_value)
                    elif _info == "DESC":
                        self.set_calib_description(_value)
                    else:
                        _msg = (
                            "Parsing Error : unknown calib field {%s} with value {%s} at line %d"
                            % (_info, _value, _line_nb)
                        )
                        raise XCalibError(_msg)

                else:
                    """
                    Read DATA line.
                    """
                    if self.get_calib_type() == "TABLE":
                        # Matches lines like: 13.000000 15.941000 (new format)
                        # ()      : save recognized group pattern
                        # [+-]?   : + or - or nothing
                        # \d      : any digit [0-9]
                        # (?: re) : Groups regular expressions without remembering matched text.
                        # \s      : Whitespace, equivalent to [\t\n\r\f].
                        matchPoint = re.search(
                            r"([+-]?\d+\.?\d*[eE]?[+-]*\d*)(?:\s+)([+-]?\d+\.?\d*[eE]?[+-]*\d*)",
                            line,
                        )

                        if not matchPoint:

                            # Matches lines like:  U35M [13.000000] = 15.941000 (legacy format)
                            # name of the calib (U35M) must be known.
                            if self.get_calib_name() is None:
                                raise XCalibError(
                                    "Parsing Error : Line %d : name of the calibration is unknown."
                                    % _line_nb
                                )
                            else:
                                # ()      : save recognized group pattern
                                # %s      : for the % subs in the string...
                                # .       : any character except a newline
                                # (?: re) : Groups regular expressions without remembering matched text.
                                # \s      : Whitespace, equivalent to [\t\n\r\f].
                                matchPoint = re.search(
                                    r"%s(?:\s*)\[(.+)\](?:\s*)=(?:\s*)(.+)"
                                    % self.get_calib_name(),
                                    line,
                                )
                                if matchPoint:
                                    self._calib_file_format = "LEGACY"

                        if matchPoint:
                            # At least one line of the calib data has been read
                            _data_line_nb = _data_line_nb + 1
                            # -> no more in header.
                            _part_letter = "D"

                            _xval = float(matchPoint.group(1))
                            _yval = float(matchPoint.group(2))
                            log.debug(
                                "line %4d%s : raw calib  : %30s   xval=%8g yval=%8g"
                                % (
                                    _line_nb,
                                    _part_letter,
                                    matchPoint.group(),
                                    _xval,
                                    _yval,
                                )
                            )
                            _nb_points = _nb_points + 1

                            _xvalues.append(_xval)
                            _yvalues.append(_yval)

                            _x_min = min(_xval, _x_min)
                            _x_max = max(_xval, _x_max)
                            _y_min = min(_yval, _y_min)
                            _y_max = max(_yval, _y_max)

                        else:
                            log.debug(
                                "line %4d%s : nomatch    : {%s}"
                                % (_line_nb, _part_letter, line.rstrip())
                            )

                    elif self.get_calib_type() == "POLY":
                        # Matches lines like :
                        # C0 = 28.78
                        matchCoef = re.search(
                            r"\s*C(\d+)\s*=\s*([-+]?\d*\.\d+|\d+)", line, re.M | re.I
                        )
                        if matchCoef:
                            _data_line_nb = _data_line_nb + 1
                            _coef = int(matchCoef.group(1))
                            _value = float(matchCoef.group(2))

                            log.debug(
                                "line %4d%s : raw calib  : %15s   coef=%8g value=%8g"
                                % (
                                    _line_nb,
                                    _part_letter,
                                    matchCoef.group(),
                                    _coef,
                                    _value,
                                )
                            )

                            _pos = self.get_calib_order() - _coef
                            # print( "_pos=", _pos)
                            self.coeffs[_pos] = _value

                    else:
                        raise XCalibError(
                            "%s line %d : invalid calib type : %s\nraw line : {%s}"
                            % (calib_source, _line_nb, self.get_calib_type(), line)
                        )

            # End of parsing of lines.

            if _data_line_nb == 0:
                raise XCalibError("No data line read in calib file.")
            else:
                self._data_lines = _data_line_nb
                log.info("DATA lines read : %d" % self._data_lines)

        except XCalibError:
            print("\n--------------- ERROR IN PARSING --------------------")
            print(sys.exc_info()[1])
            print("-E-----------------------------------------------------")
        finally:
            if _calib_file_name is not None:
                calib_source.close()

        if self.get_calib_type() == "TABLE":
            self.nb_calib_points = _nb_points
            self.Xmin = _x_min
            self.Xmax = _x_max
            self.Ymin = _y_min
            self.Ymax = _y_max
            log.info(
                " Xmin = %10g  Xmax = %10g  Nb points =%5d"
                % (self.Xmin, self.Xmax, _nb_points)
            )
            log.info(
                " Ymin = %10g  Ymax = %10g  Nb points =%5d"
                % (self.Ymin, self.Ymax, _nb_points)
            )

            # Ensure data is sorted in ascending order
            sorted_pairs = sorted(zip(_xvalues, _yvalues), key=itemgetter(0))
            _xvalues, _yvalues = [list(tuple) for tuple in zip(*sorted_pairs)]

        self.x_raw = numpy.array(_xvalues)
        self.y_raw = numpy.array(_yvalues)

        log.debug("Raw X data : %s" % ", ".join(list(map(str, self.x_raw))))
        log.debug("Raw Y data : %s" % ", ".join(list(map(str, self.y_raw))))

        if (
            self.get_calib_type() == "TABLE"
            and self.get_reconstruction_method() == "POLYFIT"
        ):
            # Fits data if needed.
            # log.info("get_calib_type=\"%s\" get_reconstruction_method=\"%s\" " %
            #         (self.get_calib_type(), self.get_reconstruction_method()))
            self.fit()
        elif (
            self.get_calib_type() == "TABLE"
            and self.get_reconstruction_method() == "INTERPOLATION"
        ):
            log.info("TABLE + INTERPOLATION => NO FIT")
        elif self.get_calib_type() == "POLY":
            log.info("POLY => NO FIT")

            # Sets Y range.
            self.Ymin = self.get_y(self.Xmin)
            self.Ymax = self.get_y(self.Xmax)

    def fit(self):
        if self.get_calib_type() == "POLY":
            print("??? no fit needed fot POLY")
            return

        if self.get_reconstruction_method() != "POLYFIT":
            print(
                "[xcalibu.py] hummm : fit not needed... (rec method=%s)"
                % self.get_reconstruction_method()
            )
            return

        _order = self.get_fit_order()
        self.coeffs = None
        self.coeffR = None

        _time0 = time.time()

        # Fits direct conversion.
        try:
            self.coeffs = numpy.polyfit(self.x_raw, self.y_raw, _order)
        except numpy.RankWarning:
            print("[xcalibu.py] not enough data")

        log.info("polynom coeffs = ")
        self.coeffs
        _o = 0
        for _c in reversed(self.coeffs):
            log.debug("Xcalibu -  polynom coeffs X%d = %s" % (_o, _c))
            _o += 1

        self.x_fitted = numpy.linspace(self.Xmin, self.Xmax, 50)
        self.y_fitted = numpy.linspace(-100, 100, 50)
        self.y_fitted = list(map(self.calc_poly_value, self.x_fitted))

        # Fits reciproque conversion.
        self.coeffR = numpy.polyfit(self.y_raw, self.x_raw, _order)

        self.x_fittedR = numpy.linspace(self.Ymin, self.Ymax, 50)
        self.y_fittedR = numpy.linspace(-100, 100, 50)
        self.y_fittedR = list(map(self.calc_fitted_reverse_value, self.x_fittedR))

        # Fit duration display.
        _fit_duration = time.time() - _time0

        if TIME_DISPLAY_FOUND:
            log.info("Fitting tooks %s" % timedisplay.duration_format(_fit_duration))
        else:
            log.info("Fitting tooks %s" % _fit_duration)

    def calc_poly_value(self, x):
        """
        x : float or numpy array of floats

        Return the Y value(s) for given X value(s) calculated using the polynom
        coefficients stored in self.coeffs list.
        Used for fitting polynoms and for POLY calibrations.
        """
        y = 0
        if self.get_calib_type() == "POLY":
            _order = self.get_calib_order()
        elif self.get_calib_type() == "TABLE":
            _order = self.get_fit_order()
        else:
            print("[xcalibu.py] calc_poly_value : ERROR in calib type")

        for ii in range(_order + 1):
            y = y + self.coeffs[_order - ii] * pow(x, ii)

        return y

    def calc_fitted_reverse_value(self, y):
        x = 0

        if self.get_calib_type() == "POLY":
            _order = self.get_calib_order()
        elif self.get_calib_type() == "TABLE":
            _order = self.get_fit_order()   # gni ???
        else:
            print("[xcalibu.py] calc_fitted_reverse_value : ERROR in calib type")

        for ii in range(_order + 1):
            x = x + self.coeffR[_order - ii] * pow(y, ii)

        return x

    def calc_interpolated_value(self, x):
        """
        Return Y value interpolated from 2 points.
        For now: only linear interpolation.
        """
        try:
            # Search if there is a matching point.
            idx = numpy.where(self.x_raw == x)[0][0]
            return self.y_raw[idx]
        except IndexError:
            # Search next point
            idx = numpy.searchsorted(self.x_raw, x, side="left")

            # If 'idx' is a boundary of the calibration, no interpolation.
            if idx >= len(self.x_raw):
                # print("Oups, found idx %d (max %d) for value %g (max %g). return max array value"%(idx, len(self.x_raw)-1, x, self.x_raw[-1]))
                return self.y_raw[len(self.x_raw)-1]
            if idx <= 0:
                # print("Oups, found idx % for value %g (min %g). return min array value"%(idx, x, self.x_raw[0]))
                return self.y_raw[0]

            x1 = self.x_raw[idx]
            x0 = self.x_raw[idx - 1]

            y0 = self.y_raw[idx - 1]
            y1 = self.y_raw[idx]

            y = y0 + (x - x0) * ((y1 - y0) / (x1 - x0))

            return y

    def save(self):
        """
        Saves current calibration into file.
        """
        _file_name = self.get_calib_file_name()

        if _file_name is None:
            print("[xcalibu.py] impossible to save : no calib file defined")
        else:
            self._save_calib_file()

    def _save_calib_file(self):
        _calib_name = self.get_calib_name()
        _file_name = self.get_calib_file_name()

        log.info("Saving calib %s in file:%s" % (_calib_name, _file_name))
        _sf = open(_file_name, mode="w+")
        _sf.write("# XCALIBU CALIBRATION\n\n")
        if _calib_name:
            _sf.write("CALIB_NAME=%s\n" % _calib_name)
        if self.get_calib_type():
            _sf.write("CALIB_TYPE=%s\n" % self.get_calib_type())
        if self.get_calib_time():
            _sf.write("CALIB_TIME=%s\n" % self.get_calib_time())
        if self.get_calib_description():
            _sf.write("CALIB_DESC=%s\n" % self.get_calib_description())
        if self.get_calib_type() == "POLY":
            _sf.write("CALIB_XMIN=%f\n" % self.min_x())
            _sf.write("CALIB_XMAX=%f\n" % self.max_x())
            _sf.write("CALIB_ORDER=%d\n" % self.get_calib_order())
        _sf.write("\n")

        # Preserve original comments in saved file
        for c in self._comments:
            if c == "# XCALIBU CALIBRATION":
                continue
            _sf.write(c)
            _sf.write("\n")

        if self.get_calib_type() == "TABLE":
            _xxx = self.get_raw_x()
            _yyy = self.get_raw_y()

            if self._calib_file_format == "LEGACY":
                for ii in range(_xxx.size):
                    _sf.write("%s[%f] = %f\n" % (_calib_name, _xxx[ii], _yyy[ii]))
            else:
                for ii in range(_xxx.size):
                    _sf.write("%f %f\n" % (_xxx[ii], _yyy[ii]))

        elif self.get_calib_type() == "POLY":
            _sf.write("CALIB_XMIN=%f\n" % self.min_x())
            _sf.write("CALIB_XMAX=%f\n" % self.max_x())
            _sf.write("CALIB_ORDER=%d\n" % self.get_calib_order())

            for ii in range(self.get_calib_order() + 1):
                _sf.write("C%d = %f\n" % (ii, self.coeffs[self.get_calib_order() - ii]))
        else:
            print("[xcalibu.py] ERROR")

        _sf.close()

    def plot(self):
        import matplotlib.pyplot as plt

        log.info("Plotting")

        if self.get_calib_type() == "POLY":
            self.x_calc = numpy.linspace(self.Xmin, self.Xmax, 50)
            self.y_calc = numpy.linspace(-100, 100, 50)
            self.y_calc = list(map(self.calc_poly_value, self.x_calc))

            print(self.x_calc)
            print(self.y_calc)
            plt.plot(self.x_calc, self.y_calc, "o", label="calculated curve")

            # first_legend = plt.legend(handles=[] , loc="best")

            plt.show()

        if self.get_calib_type() == "TABLE":
            _rec_method = self.get_reconstruction_method()

            if _rec_method == "POLYFIT":
                plt.plot(self.x_raw, self.y_raw, "o", self.x_fitted, self.y_fitted, "4")
                plt.legend(
                    [
                        "raw data(%s)" % self.get_calib_name(),
                        "fit(order=%s)" % self.get_fit_order(),
                    ],
                    loc="best",
                )
                plt.show()
            elif _rec_method == "INTERPOLATION":
                p2 = plt.plot(self.x_raw, self.y_raw, "o", label="data", linestyle="-")
                plt.show()
            else:
                log.error("plot : Unknown method : %s" % _rec_method)

    def print_table(self):
        for x, y in zip(self.x_raw, self.y_raw):
            print(x, y)

    """
    Calibration limits
    """

    def min_x(self):
        return self.Xmin

    def max_x(self):
        return self.Xmax

    def min_y(self):
        return self.Ymin

    def max_y(self):
        return self.Ymax

    """
    ???
    """

    def dataset_size(self):
        return self._data_lines

    def is_in_valid_x_range(self, x):
        """
        x: float
        Return True if <x> is in calibration boundaries.
        """
        if self.get_calib_type() == "POLY":
            return True

        if (x < (self.Xmin - 0.00001)) or (x > (self.Xmax + 0.00001)):
            log.info("Xmin=%f Xmax=%f" % (self.Xmin, self.Xmax))
            return False
        else:
            return True

    def is_in_valid_y_range(self, y):
        # humm bad : would be better to define Ymin Ymax as bounds of
        # a monoton portion of the poly...
        # but how ???
        if self.get_calib_type() == "POLY":
            return True

        if (y < (self.Ymin - 0.00001)) or (y > (self.Ymax + 0.00001)):
            log.info("Ymin=%f Ymax=%f" % (self.Ymin, self.Ymax))
            return False
        else:
            return True

    """
    Values readout
    """
    def get_y(self, x):
        """
        x: int or float or numpy array of floats.
        Return a float or a numpy array of floats.
        """
        log.debug("xcalibu - get_y(x) - type of x is: %s" % type(x))

        if type(x) == numpy.ndarray:
            return self.get_y_array(x)
        elif isinstance(x, numbers.Number):  # int float numpy.int* numpy.float*
            return self.get_y_scalar(x)
        else:
            raise TypeError(f"Type of input is invalid: {type(x)}")

    def get_y_array(self, x_arr):
        """
        x_arr: numpy array of floats
        Return a numpy array of floats
        """
        y_arr = numpy.array(list(map(self.get_y_scalar, x_arr)))
        return y_arr

    def get_y_scalar(self, x):
        """
        x: float or int
        Return a float
        """
        # log.debug("xcalibu - %s - get y of %f" % (self.get_calib_name(), x))

        if self.is_in_valid_x_range(x):
            if self.get_calib_type() == "TABLE":

                _rec_method = self.get_reconstruction_method()
                if _rec_method == "POLYFIT":
                    y = self.calc_poly_value(x)
                elif _rec_method == "INTERPOLATION":
                    y = self.calc_interpolated_value(x)
                else:
                    log.error(
                        "Unknown or not available reconstruction method : %s"
                        % _rec_method
                    )
            elif self.get_calib_type() == "POLY":
                y = self.calc_poly_value(x)
            else:
                log.error("Unknown calibration type: %s" % self.get_calib_type())

            log.debug("y=%f" % y)
            return y
        else:
            log.error(
                "xcalibu - Error : x=%f is not in valid range for this calibration" % x
            )
            raise XCalibError(
                "XValue %g out of limits [%g;%g]" % (x, self.Xmin, self.Xmax)
            )

    """
    Reciprocal calibration
    """

    def get_x(self, y):
        """
        y: int or float or numpy array of floats.
        Return a float or a numpy array of floats.
        """
        log.debug("xcalibu - get_x(y) - type of y is: %s" % type(y))

        if type(y) == numpy.ndarray:
            return self.get_x_array(y)
        elif isinstance(y, numbers.Number):  # int float numpy.int* numpy.float*
            return self.get_x_scalar(y)
        else:
            raise TypeError(f"Type of input is invalid: {type(y)}")

    def get_x_array(self, y_arr):
        """
        y_arr: numpy array of floats
        Return a numpy array of floats
        """
        x_arr = numpy.array(list(map(self.get_x_scalar, y_arr)))
        return x_arr

    def get_x_scalar(self, y):
        """
        <y>: float or int
        Return a float
        """
        log.debug("xcalibu - %s - get x of %f" % (self.get_calib_name(), y))

        # Check validity range
        if self.is_in_valid_y_range(y):
            x = self.calc_fitted_reverse_value(y)
            log.debug("x=%f" % x)
            return x
        else:
            # raise XCalibError("YValue out of limits [%g;%g]"%(self.Ymin,self.Ymax))
            log.error(
                "xcalibu - Error : y=%f is not in valid range for this R calibration"
                % y
            )
            return -1

    def delete(self, x=None, y=None):
        """
        Delete a point (x, y) in table given X or Y or both.
        """
        if x is None and y is None:
            return

        criteria = numpy.full(len(self.x_raw), True)
        if x is not None:
            criteria = criteria & (self.x_raw == x)
        if y is not None:
            criteria = criteria & (self.y_raw == y)

        index = numpy.argwhere(criteria).flatten()

        if len(index) == 0:
            raise XCalibError(f"Point ({x or ''}, {y or ''}) does not exist in table")

        if len(index) > 1:
            if x is None or y is None:
                # several points found with given X or Y. Need to give both X and Y.
                raise XCalibError(f"Ambiguous match ({len(index)} points), specify both X and Y")
            else:
                # several identical points found, delete only the first one
                index = index[0]

        log.debug(f"xcalibu - {self.get_calib_name()} - delete point ({self.x_raw[index]}, {self.y_raw[index]})")

        self.x_raw = numpy.delete(self.x_raw, index)
        self.y_raw = numpy.delete(self.y_raw, index)

        self._update_min_max_len()

    def insert(self, x, y):
        """
        Insert a point (x, y) in sorted table.

        X and Y can be float or arrays.
        """
        if self._calib_type != "TABLE":
            raise TypeError("Xcalibu: calibration must be of TABLE type")

        x = numpy.atleast_1d(x)
        y = numpy.atleast_1d(y)
        assert len(x) == len(y)

        # search index where to insert x in sorted array
        index = numpy.searchsorted(self.x_raw, x)
        self.x_raw = numpy.insert(self.x_raw, index, x)
        self.y_raw = numpy.insert(self.y_raw, index, y)

        self._update_min_max_len()

        log.debug(f"xcalibu - {self.get_calib_name()} - insert point ({x}, {y})")

    def _update_min_max_len(self):
        self._data_lines = self.nb_calib_points = len(self.x_raw)

        self.Xmin = self.x_raw[0]  # x_raw is sorted
        self.Xmax = self.x_raw[-1]
        self.Ymin = min(self.y_raw)
        self.Ymax = max(self.y_raw)


def demo(do_plot):

    log.info("============ from demo_calib_string string ===================\n")
    # loads demo calibration from demo_calib_string string
    # stored in this file with POLYFIT reconstruction method.
    myCalibString = Xcalibu(
        calib_string=demo_calib_string, fit_order=2, reconstruction_method="POLYFIT"
    )

    log.info("TEST -         demo_calib_string(%f) = %f" % (5, myCalibString.get_y(5)))
    log.info("TEST - inverse_demo_calib_string(%f) = %f" % (4, myCalibString.get_x(4)))

    log.info("============= POLY calibration from file ========================\n")
    myCalibPoly = Xcalibu(calib_file_name=XCALIBU_DIRBASE + "/examples/poly.calib")
    log.info("xcalibu - TEST - Gap for %f keV : %f" % (5, myCalibPoly.get_y(5)))

    log.info(
        "====== undu TABLE calibration from file with POLYFIT reconstruction method ====\n"
    )
    myCalib2 = Xcalibu(
        calib_file_name=XCALIBU_DIRBASE + "/examples/undu_table.calib",
        fit_order=2,
        reconstruction_method="POLYFIT",
    )

    log.info("TEST - Gap for %f keV : %f" % (5, myCalib2.get_y(5)))

    log.info(
        "===== undu TABLE calibration from file with INTERPOLATION rec. method ======\n"
    )
    myCalib3 = Xcalibu(
        calib_file_name=XCALIBU_DIRBASE + "/examples/table.calib",
        fit_order=2,
        reconstruction_method="INTERPOLATION",
    )

    log.info("TEST - Gap for %f keV : %f" % (1, myCalib3.get_y(1)))
    log.info("TEST - Gap for %f keV : %f" % (2, myCalib3.get_y(2)))
    log.info("TEST - Gap for %f keV : %f" % (4, myCalib3.get_y(4)))
    log.info("TEST - Gap for %f keV : %f" % (9, myCalib3.get_y(9)))
    # errors :
    log.info("TEST - Gap for %f keV : %f" % (0.5, myCalib3.get_y(0.5)))
    log.info("TEST - Gap for %f keV : %f" % (12, myCalib3.get_y(12)))

    myCalibRingTx = Xcalibu(
        calib_file_name=XCALIBU_DIRBASE + "/examples/hpz_ring_Tx.calib",
        fit_order=5,
        reconstruction_method="POLYFIT",
    )

    myCalibRingTy = Xcalibu(
        calib_file_name=XCALIBU_DIRBASE + "/examples/hpz_ring_Ty.calib",
        fit_order=4,
        reconstruction_method="POLYFIT",
    )

    myCalibCubic = Xcalibu(
        calib_file_name=XCALIBU_DIRBASE + "/examples/cubic.calib",
        fit_order=3,
        reconstruction_method="POLYFIT",
    )

    myCalibRingTz = Xcalibu(
        calib_file_name=XCALIBU_DIRBASE + "/examples/hpz_ring_Tz.calib",
        fit_order=20,
        reconstruction_method="POLYFIT",
    )

    myCalibRingRx = Xcalibu(
        calib_file_name=XCALIBU_DIRBASE + "/examples/hpz_ring_Rx.calib",
        fit_order=5,
        reconstruction_method="POLYFIT",
    )

    myCalibRingRy = Xcalibu(
        calib_file_name=XCALIBU_DIRBASE + "/examples/hpz_ring_Ry.calib",
        fit_order=5,
        reconstruction_method="POLYFIT",
    )

    #     print("saving poly demo....",)
    #     myCalib1.set_calib_file_name("ppp.calib")
    #     myCalib1.save()
    #     print("OK")
    #     print("------------------------------------------------------------------------------")

    print("saving table demo....")
    myCalibRingRy.set_calib_file_name("ttt.calib")
    myCalibRingRy.save()
    print("OK")
    print("---------------------------------------------------------------------------")

    print("Example : creation of an empty calib then populate it with in-memory data")
    myDynamicCalib = Xcalibu()
    myDynamicCalib.set_calib_file_name("ddd.calib")
    myDynamicCalib.set_calib_type("TABLE")
    myDynamicCalib.set_reconstruction_method("INTERPOLATION")
    myDynamicCalib.set_calib_time("1234.5678")
    myDynamicCalib.set_calib_description("dynamic calibration created for demo")
    myDynamicCalib.set_raw_x(numpy.linspace(1, 10, 10))
    myDynamicCalib.set_raw_y(numpy.array([3, 6, 5, 4, 2, 5, 7, 3, 7, 4]))
    myDynamicCalib.save()
    print("myDynamicCalib.get_y(2.3)=%f" % myDynamicCalib.get_y(2.3))
    print("---------------------------------------------------------------------------")
    print("---------------------------------------------------------------------------")
    print("---------------------------------------------------------------------------")

    print(dir(myCalibCubic))
    print(myCalibCubic.coeffs)

    print("---------------------------------------------------------------------------")
    print("---------------------------------------------------------------------------")
    print("---------------------------------------------------------------------------")

    if do_plot:
        # myCalib1.plot()
        # myCalib2.plot()
        # myCalib3.plot()
        # myCalibRingTx.plot()
        myCalibRingTy.plot()
        myDynamicCalib.plot()
        myCalibCubic.plot()
        # myCalibRingTz.plot()
        # myCalibRingRx.plot()
        # myCalibRingRy.plot()


def main():
    """
    main function is provided for demonstration and testing purposes.
    """
    print("")
    print("------------------------{ Xcalibu }----------------------------------")

    """
    arguments parsing
    """
    from optparse import OptionParser

    parser = OptionParser("xcalibu.py")
    parser.add_option(
        "-d",
        "--debug",
        type="string",
        help="Available levels are :\n CRITICAL(50)\n \
                      ERROR(40)\n WARNING(30)\n INFO(20)\n DEBUG(10)",
        default="INFO",
    )

    parser.add_option(
        "-p",
        "--plot",
        action="store_true",
        dest="plot",
        default=False,
        help="Plots calibration",
    )

    # Gathers options and arguments.
    (options, args) = parser.parse_args()
    # print(options)
    # print(args)

    """
    Log level
    """
    try:
        loglevel = getattr(logging, options.debug.upper())
    except AttributeError:
        # print "AttributeError  o.d=",options.debug
        loglevel = {
            50: logging.CRITICAL,
            40: logging.ERROR,
            30: logging.WARNING,
            20: logging.INFO,
            10: logging.DEBUG,
        }[int(options.debug)]

    print(
        "[xcalibu] - log level = %s (%d)" % (logging.getLevelName(loglevel), loglevel)
    )
    logging.basicConfig(format=LOG_FORMAT, level=loglevel)

    if len(args) == 0:
        parser.print_help()
        print("")
        print("Argument:")
        print("  demo                  Launche some examples of calibrations")
        print(
            "  <calib_file>          Launche demo using <calib_file> calibration file"
        )
        print("")
    else:

        if args[0] == "demo":
            demo(options.plot)

        else:
            print('use "%s" argument as calib test file' % args[0])
            # loads calibration from file.
            myCalib = Xcalibu(
                calib_file_name=args[0],
                fit_order=3,
                reconstruction_method="INTERPOLATION",
            )

            # Some calib parameters:
            _xmin = myCalib.min_x()
            _xmax = myCalib.max_x()
            _xrange = _xmax - _xmin

            # Example : calculation of middle point (X range) of calibration.
            _xtest = (_xmin + _xmax) / 2
            _time0 = time.time()
            _ytest = myCalib.get_y(_xtest)
            _calc_duration = time.time() - _time0

            if TIME_DISPLAY_FOUND:
                _calc_duration = timedisplay.duration_format(_calc_duration)

            log.info("y value of %g = %g (%s)" % (_xtest, _ytest, _calc_duration))

            _NB_POINTS = 25
            # bench example : calculation of _NB_POINTS points.
            _time0 = time.time()
            for xx in numpy.arange(_xmin, _xmax, _xrange / _NB_POINTS):
                yy = myCalib.get_y(xx)
                # print( " f(%06.3f)=%06.3f   "%(xx, yy),)
            _Ncalc_duration = time.time() - _time0

            if TIME_DISPLAY_FOUND:
                _Ncalc_duration = timedisplay.duration_format(_Ncalc_duration)

            log.info(
                "Calculation of %d values of y. duration : %s"
                % (_NB_POINTS, _Ncalc_duration)
            )

            sys.stdout.flush()

            if options.plot:
                myCalib.plot()


demo_calib_string = """
# TEST calibration
# Type TABLE
# Comments are starting with '#'
# Spaces are mainly ignored.

CALIB_NAME = B52
CALIB_TYPE = TABLE
CALIB_TIME = 1400081171.300155
CALIB_DESC = 'test table : example of matching lines'
#CALIB_TITI = 14

B52[0.8e-2] = -0.83e-2
B52[1]=1
B52[3]= 2
B52[5]=-12
B52 [6]=  -3
B52 [7]=   2
B52[10]=   4.5
 B52[13]=7.5
   B52[15]=18.5
B52[18]=0.5e2
B52[23]=	42
B52[23.1]=0.61e2
B52[27.401] = 0.72e2
B52[32]=  62
B52[0.5e2] = +0.53e2
"""

if __name__ == "__main__":
    main()
