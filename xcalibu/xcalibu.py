#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# xcalibu.py
# Calibration Manager
#
# Xcalibu is python code to deal with calibrations data:
#  * load / save from file, string, list, numpy array
#  * fit tables (using numpy)
#  * interpolate (using scipy)
#
# The Xcalibu class mainly provides the following method :
#   get_y(x) which returns the f(x) fitted value.
#
# If using TABLE, the class can perform the fit of the raw data and
# furnishes a y=f(x) polynomial function.
#
# The returned value is calculated by various reconstruction methods
# depending on the calibration type and parameters.
#   TABLE ----> INTERPOLATION   |  POLYFIT
#   POLY  ----> POLY (Direct calculation)
#
# The reverse function "get_x(y)" is also available.
# Take care : get_x(get_y(x)) can be different from x due to
# approximation.
#
# Meta-data of a calibration (fixed at calib recording/generation) are:
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
#
# Ndp: https://www.desmos.com/calculator?lang=fr


import logging
import numbers
import numpy
from numpy.polynomial.polynomial import Polynomial
from operator import itemgetter
import os
import re
from scipy import interpolate
import sys
import time


try:
    import timedisplay

    TIME_DISPLAY_FOUND = True
except ImportError:
    TIME_DISPLAY_FOUND = False

log = logging.getLogger("XCALIBU")
LOG_FORMAT = "%(name)s - %(levelname)s - %(message)s"

XCALIBU_DIRBASE = os.path.dirname(os.path.realpath(__file__))

__all__ = ["Xcalibu", "XCalibError"]


SAMPLING_NB_POINTS = 40


class XCalibError(Exception):
    """Custom exception class for Xcalibu."""

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return "XCALIBU error: %s" % self.message


class Xcalibu:
    def __init__(
        self,
        calib_name=None,
        calib_string=None,
        calib_file_name=None,
        calib_type=None,
        fit_order=None,
        coeffs=None,
        polynomial=None,
        reconstruction_method=None,
        interpol_kind="linear",
        description=None
    ):

        # Default parameters (accessible via constructor)
        self._calib_name = calib_name
        self._calib_string = None
        self._calib_file_name = None
        self._calib_type = None
        self._fit_order = 0
        self._poly_coeffs = coeffs    # list of Polynomial coefficients (increasing degree: numpy Polynomial rule)
        self._polynomial = None       # numpy Polynomial object
        self._rec_method = None
        self._interpol_kind = "linear"

        # internal parameters
        self._calib_time = None
        self._description = description
        self._calib_order = 0  # Order of the polynom used for POLY calibrations.
        self._calib_file_format = "XCALIBU"  # "TWO_COLS" | "ONE_COL"
        self.is_monotonic = None
        self.is_increasing = None

        self.Xmin = numpy.nan
        self.Xmax = numpy.nan
        self.Ymin = numpy.nan
        self.Ymax = numpy.nan

        self._data_lines = 0
        self._comments = []

        """
        Constructor parameters recording
        """
        # Calib name
        if calib_name is not None:
            self.set_calib_name(calib_name)

        # Calib string.
        if calib_string is not None:
            self.set_calib_string(calib_string)
            # print("calib string found:", calib_string[0:20])

        # Calib file name.
        if calib_file_name is not None:
            self.set_calib_file_name(calib_file_name)

        # Calib Type
        if calib_type is not None:
            self.set_calib_type(calib_type)

        # Polynom order to be used by reconstruction method for TABLE calibrations.
        if fit_order is not None:
            self.set_fit_order(fit_order)

        # Coeffs
        if coeffs is not None:
            self.set_coeffs(coeffs)

        # Reconstruction method for TABLE calibrations of for reverse POLY.
        # * INTERPOLATION : interpolation segment by segment.
        # * POLYFIT : polynomial fitting of the dataset.
        if reconstruction_method is not None:
            self.set_reconstruction_method(reconstruction_method, interpol_kind)

        # Description
        if description is not None:
            self.set_calib_description(description)

        # Load if data are available.
        if (
            self.get_calib_file_name() is not None
            or self.get_calib_string() is not None
        ):
            # A calib string or a file name is defined, try to load the calib.
            self.load_calib()
            self.check_monotonic()
            self.compute_interpolation()

    def compute_interpolation(self):
        """
        Compute interoplation function if reconstruction method is INTERPOLATION.
        If possible (ie: monotonic on interval), compute reverse interpolation function.
        """

        if self.get_reconstruction_method() == "INTERPOLATION":
            log.info("compute_interpolation()")

            # raw data arrays must be filled for POLY.
            if self.get_calib_type() == "POLY":
                self.x_raw = numpy.linspace(self.Xmin, self.Xmax, SAMPLING_NB_POINTS)
                self.y_raw = self.calc_poly_value(self.x_raw)

            print("========================================")
            print(self.x_raw)
            print(self.y_raw)
            print(self.get_interpol_kind())
            print("========================================")
            self.ifunc = interpolate.interp1d(self.x_raw, self.y_raw,
                                              kind=self.get_interpol_kind(),
                                              bounds_error=False, fill_value=999.999)
            if self.is_monotonic:
                log.info("compute_interpolation() reverse")

                self.ifuncR = interpolate.interp1d(self.y_raw, self.x_raw,
                                                   kind=self.get_interpol_kind(),
                                                   bounds_error=False, fill_value=666.666)
            else:
                self.ifuncR = None
        else:
            log.info(f"cannot compute_interpolation() (rec method = {self.get_reconstruction_method()}")

    def check_monotonic(self):
        """
        Check if calibration is monotonic.
        ie: y_raw values are strictly increasing or strictly decreasing.
        set 'is_monotonic' boolean.
        """

        if self.get_calib_type() == "TABLE":
            # print(self.y_raw)
            y_diff = numpy.diff(self.y_raw)
            # print(y_diff)

            if numpy.all(y_diff > 0):
                self.is_monotonic = True
                self.is_increasing = True
                print("calib is MONOTONIC INCREASING")
            elif numpy.all(y_diff < 0):
                self.is_monotonic = True
                self.is_increasing = False
                print("calib is MONOTONIC DECREASING")
            else:
                self.is_monotonic = False
                self.is_increasing = None
                print("calib is NOT monotonic")

        if self.get_calib_type() == "POLY":
            log.info(f"check if poly is monotonic on {self.Xmin} {self.Xmax}")

            # Calculate the derivative polynom.
            # print("poly = ", self._polynomial)
            self._poly_deriv = self._polynomial.deriv()
            log.debug(f"derivative poly = {self._poly_deriv.__str__()}")

            # All roots including imaginary ones.
            roots = self._poly_deriv.roots()
            log.debug("Roots of the derivative polynom:")
            log.debug(roots)

            # Real roots only
            real_roots = roots.real[abs(roots.imag) < 1e-6]
            # print("Real Roots = ", real_roots)

            # Real roots in limits only
            real_valid_roots = [x for x in real_roots if x > self.Xmin and x < self.Xmax]

            # real_valid_roots
            if len(real_valid_roots) == 0:
                self.is_monotonic = True
                log.info(f"This poly is monotonic on [{self.Xmin};{self.Xmax}] ")
            else:
                self.is_monotonic = False
                log.info(f"This poly is not monotonic on [{self.Xmin};"
                      f"{self.Xmax}] (real root(s) of the derivative: {real_valid_roots})")

    def set_calib_file_name(self, fn):
        """
        Set name of the file to use to load/save a calibration.
        """
        log.debug("set_calib_file_name(%s)" % fn)
        self._calib_file_name = fn
        print(f"Calib file name set to: \"{self.get_calib_file_name()}\"")

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
        print(f"calib name set to: \"{self.get_calib_name()}\"")

    def get_calib_name(self):
        """
        Calibration name is read from the calibration file or string (field : CALIB_NAME).
        """
        return self._calib_name

    def set_calib_type(self, value):
        """
        Set calibration type read from calibration file or string (field : CALIB_TYPE)
        or passe das command line argument.
        Can be 'TABLE' or 'POLY'.
        """
        if value == "TABLE":
            self._calib_type = value
        elif value == "POLY":
            self._calib_type = value
            # self.set_reconstruction_method("POLY")
        else:
            raise ValueError(f"wrong calib type: {value}")

        print(f"calib type set to: \"{self.get_calib_type()}\"")

    def get_calib_type(self):
        """
        Return calibration type read from calibration file or string (field : CALIB_TYPE).
        Can be 'TABLE' or 'POLY'.
        """
        return self._calib_type

    def set_fit_order(self, order):
        """
        Fit order used to fit TABLE calibrations.
        """
        if isinstance(order, int) and order > 0:
            self._fit_order = order
            print(f"fit order set to: {self.get_fit_order()}")
        else:
            log.error("set_fit_order : <fit_order> must be a positive integer.")

    def get_fit_order(self):
        return self._fit_order

    def set_calib_time(self, timestamp):
        """
        time of creation of the calibration (seconds since epoch)
        """
        self._calib_time = timestamp

    def get_calib_time(self):
        return self._calib_time

    """
    Set order of polynomia used to define calibration (NOT TO FIT).
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

    def set_interpol_kind(self, value):
        """
        Set kind of interpolation to use to interpolate values in TABLE calibrations.
        <kind>: str: kind of interpolation according to scipy interpolation methods:
                     https://www.tutorialspoint.com/scipy/scipy_interpolate.htm
                     ex: 'linear', 'quadratic', 'cubic'
        """
        self._interpol_kind = value.lower()
        print(f"interpol_kind set to: \"{self.get_interpol_kind()}\"")

    def get_interpol_kind(self):
        return self._interpol_kind

    def set_interpol_fill_value(self, value):
        """
        Set value to return when query value is outside TABLE limits.
        <value>: float
        """
        self._fill_value = value

    def get_interpol_fill_value(self):
        return self._fill_value

    """
    x raw data numpy array.
    """

    def set_raw_x(self, arr_x):
        self.x_raw = arr_x
        self.Xmin = self.x_raw.min()
        self.Xmax = self.x_raw.max()

    def get_raw_x(self):
        return self.x_raw

    def set_raw_y(self, arr_y):
        """
        Set y raw data numpy array.
        """
        self.y_raw = arr_y
        self.Ymin = self.y_raw.min()
        self.Ymax = self.y_raw.max()

    def get_raw_y(self):
        return self.y_raw

    """
    calibration USAGE parameters.
    """

    def set_reconstruction_method(self, method, kind=None):
        """
        Set method to retreive y data from x data : can be 'INTERPOLATION' , 'POLYFIT' or 'POLY'
        """
        if method in ["INTERPOLATION", "POLYFIT"]:
            self._rec_method = method
            if method == "INTERPOLATION":
                if kind is not None:
                    self.set_interpol_kind(kind)
                else:
                    print("NO KIND ???")
        elif method == "POLY":
            self._rec_method = method
        else:
            raise XCalibError("unknown method : %s " % method)

        print(f"reconstruction methode set to: \"{self.get_reconstruction_method()}\"")

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

        _coeffs_dict = {}

        _calib_file_name = self.get_calib_file_name()
        _calib_string = self.get_calib_string()

        if _calib_file_name is not None:
            try:
                calib_source = open(_calib_file_name, mode="r")
                print(f"open file: {_calib_file_name}")
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

                # Match lines like :
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
                        self._poly_coeffs = numpy.zeros(self.get_calib_order() + 1)
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
                    NdP: https://regex101.com/  :)
                    """
                    if self.get_calib_type() == "TABLE":

                        # Match lines like: 13.123000  (1 column format)
                        matchPoint = re.search(
                            r"^([+-]?\d+\.?\d*[eE]?[+-]*\d*)$",
                            line,
                        )

                        if matchPoint:
                            log.debug("matched ONE_COL")
                            self._calib_file_format = "ONE_COL"
                        else:
                            # Match lines like: 13.000000 15.941000 (2 columns format)
                            # ()      : save recognized group pattern
                            # [+-]?   : + or - or nothing
                            # \d      : any digit [0-9]
                            # (?: re) : Groups regular expressions without remembering matched text.
                            # \s      : Whitespace, equivalent to [\t\n\r\f].
                            matchPoint = re.search(
                                r"^([+-]?\d+\.?\d*[eE]?[+-]*\d*)(?:\s+)([+-]?\d+\.?\d*[eE]?[+-]*\d*)$",
                                line,
                            )

                            if matchPoint:
                                log.debug("matched TWO_COLS")
                                self._calib_file_format = "TWO_COLS"
                            else:

                                # Match lines like:  U35M [13.000000] = 15.941000 (XCALIBU format)
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
                                        log.debug("matched XCALIBU")
                                        self._calib_file_format = "XCALIBU"

                        if matchPoint:
                            # At least one line of the calib DATA has been read
                            _data_line_nb = _data_line_nb + 1
                            # -> no more in header.
                            _part_letter = "D"

                            try:
                                _xval = float(matchPoint.group(1))
                                _yval = float(matchPoint.group(2))
                            except:
                                _xval = _data_line_nb
                                _yval = float(matchPoint.group(1))

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
                            _coeff = int(matchCoef.group(1))
                            _value = float(matchCoef.group(2))

                            log.debug(
                                "line %4d%s : raw calib  : %15s   coef=%8g value=%8g"
                                % (
                                    _line_nb,
                                    _part_letter,
                                    matchCoef.group(),
                                    _coeff,
                                    _value,
                                )
                            )

                            # Fill temporary dict.
                            log.debug(f"------ _coeff={_coeff}  _value={_value}")
                            _coeffs_dict[_coeff] = _value

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

        log.info("Raw X data : %s" % ", ".join(list(map(str, self.x_raw))))
        log.info("Raw Y data : %s" % ", ".join(list(map(str, self.y_raw))))

        if self.get_calib_type() == "TABLE":
            if self.get_reconstruction_method() == "POLYFIT":
                self.fit()

            if self.get_reconstruction_method() == "INTERPOLATION":
                log.info("TABLE + INTERPOLATION => NO FIT")

        elif self.get_calib_type() == "POLY":
            # Set Y range.

            _declared_order = self.get_calib_order()

            if len(_coeffs_dict) == _declared_order + 1:
                print(_coeffs_dict)

                _coeff_list = [0] * len(_coeffs_dict)

                for coef, val in _coeffs_dict.items():
                    _coeff_list[coef] = val

                print(f"_coeff_list = {_coeff_list}")

                self.set_coeffs(_coeff_list)
                self.Ymin = self.get_y(self.Xmin)
                self.Ymax = self.get_y(self.Xmax)
            else:
                raise ValueError(f"len(_coeffs_dict)+1={len(_coeffs_dict)+1}  _declared_order={_declared_order}")

    def set_coeffs(self, coeffs):
        """
        Set coefficients of a POLY calib
        <coeffs>: list: [C0, C1, .., CN] in order of increasing degree (numpy Polynomial rule)
        ex: []  --->   -8.0 - 6.0·x¹ + 3.0·x² + 1.0·x³

        * Order is calculated from length of coeffs list.
        * Create Polynomial
        """
        self.set_calib_order(len(coeffs) - 1)

        self._poly_coeffs = coeffs.copy()

        self._polynomial = Polynomial(self._poly_coeffs)
        print(self._polynomial)

    def get_coeffs(self, order=None):
        """
        Return coeffs of a POLY table.
        if <order> is specified, return the corresponding coefficient.
        """
        if order is not None:
            return self._poly_coeffs[order]
        else:
            return self._poly_coeffs

    def set_x_limits(self, xmin, xmax):
        """
        """
        self.Xmin = xmin
        self.Xmax = xmax

    def fit(self):
        """
        Fit raw data if needed.
        """
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
        self._poly_coeffs = numpy.zeros(_order + 1)

        # ??
        self.coeffR = None

        _time0 = time.perf_counter()

        # Fit direct conversion.
        try:
            # Numpy polyfit
            # self._poly_coeffs = list(numpy.polyfit(self.x_raw, self.y_raw, _order))
            # self._poly_coeffs.reverse()   # polyfit return coeffs in descending order.
            # print("NUMPY POLYFIT=", self._poly_coeffs)

            # Calculate Numpy Polynomial and fit coeffs.
            self._polynomial = numpy.polynomial.polynomial.Polynomial.fit(
                self.x_raw,
                self.y_raw,
                _order,
                window=[self.Xmin, self.Xmax]
                )
            print("Polynomial  =", self._polynomial)
            self._poly_coeffs = list(self._polynomial.coef)

        except numpy.RankWarning:
            print("[xcalibu.py] not enough data")

        self.x_fitted = numpy.linspace(self.Xmin, self.Xmax, 50)
        self.y_fitted = numpy.linspace(-100, 100, 50)
        self.y_fitted = list(map(self.calc_poly_value, self.x_fitted))

        # Fit reciprocal conversion ???
        self.coeffR = numpy.polyfit(self.y_raw, self.x_raw, _order)

        self.x_fittedR = numpy.linspace(self.Ymin, self.Ymax, 50)
        self.y_fittedR = numpy.linspace(-100, 100, 50)
        self.y_fittedR = list(map(self.calc_reverse_value, self.x_fittedR))

        # Fit duration display.
        _fit_duration = time.perf_counter() - _time0

        if TIME_DISPLAY_FOUND:
            log.info("Fitting tooks %s" % timedisplay.duration_format(_fit_duration))
        else:
            log.info("Fitting tooks %s" % _fit_duration)

    def calc_poly_value(self, x):
        """
        x : float or numpy array of floats

        Return the Y value(s) for given X value(s) calculated using the polynom coefficients.
        Used for POLY and TABLE (once fitted) calibrations.
        """
        y = 0
        if self.get_calib_type() == "POLY":
            _order = self.get_calib_order()
        elif self.get_calib_type() == "TABLE":
            _order = self.get_fit_order()
        else:
            print("[xcalibu.py] calc_poly_value : ERROR in calib type")

        for ii in range(_order + 1):
            y = y + self._poly_coeffs[ii] * pow(x, ii)

        return y

    def calc_reverse_value(self, y):
        """
        Calculate reverse value if possible (ie: monotonic)

        TABLE: use reverse interpolation function (ifuncR)
        POLY: use reverse poly  or reverse interpolation function

        """
        x = 0

        if self.get_calib_type() == "POLY":
            if self.get_reconstruction_method() == "INTERPOLATION" and self.is_monotonic:
                return self.ifuncR(y)
            else:
                _order = self.get_calib_order()
                for ii in range(_order + 1):
                    x = x + self.coeffR[_order - ii] * pow(y, ii)
                return x

        elif self.get_calib_type() == "TABLE":
            if self.get_reconstruction_method() == "INTERPOLATION" and self.is_monotonic:
                return self.ifuncR(y)
            else:
                _order = self.get_fit_order()
                for ii in range(_order + 1):
                    x = x + self.coeffR[_order - ii] * pow(y, ii)
                return x

        else:
            print("[xcalibu.py] calc_reverse_value : ERROR in calib type")

    def calc_interpolated_value(self, x):
        """
        Return interpolated Y value
        """
        return self.ifunc(x)

    def calc_interpolated_valueR(self, y):
        """
        Return interpolated X value from y
        """
        return self.ifuncR(y)

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

            if self._calib_file_format == "XCALIBU":
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
                _sf.write("C%d = %f\n" % (ii, self._poly_coeffs[ii]))
        else:
            print("[xcalibu.py] ERROR")

        _sf.close()

    def plot(self):
        """
        Use matplotlib to display calibration curve.
        """
        # Load matplotlib but don't want matplotlib debug
        logging.getLogger().setLevel("INFO")
        import matplotlib.pyplot as plt
        import matplotlib
        print(f"matplotlib version {matplotlib.__version__}")

        if self.get_calib_type() == "POLY":

            log.info(f"Plotting POLY={self._polynomial} ; "
                     f"desc={self.get_calib_description()} ; name={self.get_calib_name()}")

            self.x_calc = numpy.linspace(self.Xmin, self.Xmax, SAMPLING_NB_POINTS)
            self.y_calc = self.get_y_array(self.x_calc)

            # print("x_calc=", self.x_calc)
            # print("y_calc=", self.y_calc)
            # print("calib order=", self.get_calib_order())
            fig, ax = plt.subplots()
            _ = plt.plot(self.x_calc, self.y_calc, "--")
            _ = plt.plot(self.y_calc, self.x_calc, "--")

            ax.set_xlabel('my xdata')
            ax.set_ylabel('my ydata')

            l1 = (f"POLY={self._polynomial} ({self.get_calib_name()})  \n"
                  f"desc={self.get_calib_description()}")
            l2 = "reverse"
            ax.legend([l1, l2], loc="best")
            plt.show()

        elif self.get_calib_type() == "TABLE":
            log.info(f"Plotting TABLE ; desc={self.get_calib_description()} ; name={self.get_calib_name()}")
            _rec_method = self.get_reconstruction_method()

            if _rec_method == "POLYFIT":
                plt.plot(self.x_raw, self.y_raw, "o", self.x_fitted, self.y_fitted, "4")
                plt.legend(["raw data(%s)" % self.get_calib_name(),
                            "fit(order=%s)" % self.get_fit_order(), ], loc="best", )
                plt.show()
            elif _rec_method == "INTERPOLATION":
                plt.plot(self.x_raw, self.y_raw, "o", label="data", linestyle="-")

                # if self.is_monotonic:
                #    # compute reverse plot
                #    x_rawR =
                #    y_rawR =

                plt.legend(["INTERPOLATION raw data(%s)" % self.get_calib_name(), ], loc="best", )
                plt.show()
            else:
                log.error("plot : Unknown method : %s" % _rec_method)

        else:
            print("OH OH do not know this calib type :(")

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
        elif isinstance(y, numbers.Number):  # test ok for : int float numpy.int* numpy.float*
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
            x = self.calc_reverse_value(y)
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


def main():
    """
    main function for command line usage.
    """

    print("")
    print("--------------------------------{ Xcalibu }----------------------------------")

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
        "-n",
        "--name",
        dest="name",
        type="string",
        default="My Calib",
        help="Calibration name",
    )

    parser.add_option(
        "-p",
        "--plot",
        action="store_true",
        dest="plot",
        default=False,
        help="Calibration plotting",
    )

    parser.add_option(
        "-t",
        "--type",
        dest="type",
        type="string",
        default="TABLE",
        help="Type of calibration: TABLE or POLYNOM",
    )

    parser.add_option(
        "-r",
        "--reconstruction_method",
        dest="reconstruction_method",
        type="string",
        default="INTERPOLATION",
        help="Reconstruction method: FIT or INTERPOLATION",
    )

    parser.add_option(
        "-k",
        "--kind",
        dest="kind_interpol",
        type="string",
        default="linear",
        help="Kind of interpolation: linear, cubic, quadratic etc...",
    )

    parser.add_option(
        "-f",
        "--fit_order",
        dest="fit_order",
        type=int,
        default=3,
        help="Fit order for data fitting",
    )

    # Gather options and arguments.
    (options, args) = parser.parse_args()

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
        print(
            "  <calib_file>          Load <calib_file> calibration file"
        )
        print("")
    else:

        file_name = args[0]

        print("using '{file_name}' argument as calib test file")
        # load calibration from file.

        print("--------------args------------------------")
        print(options)
        print(" type=", options.type)
        print(" name=", options.name)
        print(" kind=", options.kind_interpol)
        print(" rec_method=", options.reconstruction_method)
        print(" fit_order=", options.fit_order)
        print("--------------------------------------")

        try:
            myCalib = Xcalibu(calib_name=options.name,
                              calib_file_name=file_name,
                              fit_order=options.fit_order,
                              reconstruction_method=options.reconstruction_method,
                              interpol_kind=options.kind_interpol,
                              )
        except XCalibError as xcaliberr:
            print(f"\nERROR: {xcaliberr.message}")
            sys.exit(0)

        print("--------------------------------------------------")
        # Some calib parameters:
        _xmin = myCalib.min_x()
        _xmax = myCalib.max_x()
        _xrange = _xmax - _xmin

        # Example : calculation of middle point (X range) of calibration.
        _xtest = (_xmin + _xmax) / 2
        _time0 = time.perf_counter()
        _ytest = myCalib.get_y(_xtest)
        _calc_duration = time.perf_counter() - _time0

        if TIME_DISPLAY_FOUND:
            _calc_duration = timedisplay.duration_format(_calc_duration)

        log.info("y value of %g = %g (%s)" % (_xtest, _ytest, _calc_duration))

        # bench example : calculation of some points.
        _time0 = time.perf_counter()
        for xx in numpy.arange(_xmin, _xmax, _xrange / SAMPLING_NB_POINTS):
            yy = myCalib.get_y(xx)
            # print( " f(%06.3f)=%06.3f   "%(xx, yy),)
        _Ncalc_duration = time.perf_counter() - _time0

        if TIME_DISPLAY_FOUND:
            _Ncalc_duration = timedisplay.duration_format(_Ncalc_duration)

        log.info(
            "Calculation of %d values of y. duration : %s"
            % (SAMPLING_NB_POINTS, _Ncalc_duration)
        )

        if myCalib.is_monotonic:
            print("--------- Reverse computation ----------")
            print(f"xmin={myCalib.Xmin} xmax={myCalib.Xmax}")

            y_min = myCalib.get_y(myCalib.Xmin)
            y_max = myCalib.get_y(myCalib.Xmax)
            y_middle = (y_max + y_min) / 2
            print(f"y_min={y_min} y_max={y_max}   y_middle={y_middle}")
            print(f"myCalib.get_x({y_middle})={myCalib.get_x(y_middle)}")

            yy = numpy.linspace(y_min, y_max, SAMPLING_NB_POINTS)
            xx = myCalib.get_x(yy)
            yyy = myCalib.get_y(xx)
            diff = yy-yyy
            for ii in range(len(yy)):
                print(f"{yy[ii]:.15f} -> {xx[ii]:.15f} -> {yyy[ii]:.15f}  diff={diff[ii]:.15f}")
            print(f"max diff= {max(diff)}")

            # SAMPLING_NB_POINTS =   40 -> max diff= 0.0363018
            # SAMPLING_NB_POINTS =  400 -> max diff= 0.0003790
            # SAMPLING_NB_POINTS = 4000 -> max diff= 0.0000038 = 3.8e-06

        if options.plot:
            try:
                myCalib.plot()
            except KeyboardInterrupt:
                print("bye bye")


if __name__ == "__main__":
    main()
