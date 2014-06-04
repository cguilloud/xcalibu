#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# xcalibu.py
# Generic Calibration Manager
#
# Xcalibu is a class to deal with calibrations.
#
# The calibration is read from a file storing information as a table
# or as a polynom.
#
#   ex of field of a table : U32BC1G[5.00]=14.05
#
# If using table, the class performs the fit of the raw data and
# furnishes a y=f(x) polynomial function.
#
# The class mainly provides the following method :
#
#   get_y(x) which returns the f(x) fitted value.
#
# The fit orded can be set.
# The reverse function "get_x(y)" is also available.
# Take care : get_x(get_y(x)) can not be x due to approximation of
# fitting.

__author__  = "cyril.guilloud@esrf.fr"
__date__    = "2012 - 2013 - 2014"
__version__ = "0.03"

# imports python
import sys
import numpy
import time
import re
import matplotlib.pyplot as plt


# logging
import logging
log = logging.getLogger("XCALIBU")
LOG_FORMAT = '%(name)s - %(levelname)s - %(message)s'


class XCalibError(Exception):
    """Custom exception class for Xcalibu."""
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return "XCALIBU error: %s" % self.message


class Xcalibu:
    Xmin = 0
    Xmax = 0
    Ymin = 0
    Ymax = 0
    x = None
    y = None
    _method = None

    def __init__(self, calib_file_name=None, fit_order=None, method=None):

        self._calib_name = None
        self._calib_type = None
        self._calib_order = None
        self._fit_order = None

        # Poly order to be used by reconstruction method for TABLE calibrations.
        if fit_order:
            self._fit_order = fit_order

        # Reconstruction method for TABLE calibrations.
        # *INTERPOLATION : interpolation segment by segment.
        # or
        # *POLYFIT : polynomial fitting of dataset.
        if method:
            self._method = method


        # Try to open calib file.
        try:
            _cf = open(calib_file_name, mode='r')
        except IOError:
            log.critical("Xcalibu : Unable to open file %s \n" % calib_file_name)
            _cf.close()
            sys.exit(-1)
        except:
            sys.excepthook(sys.exc_info()[0],
                           sys.exc_info()[1],
                           sys.exc_info()[2])
            _cf.close()

        # Ok file exists.
        try:
            self.load_calib(_cf)
        except:
            print "error in calibration loading --> exit"
            sys.excepthook(sys.exc_info()[0],
                           sys.exc_info()[1],
                           sys.exc_info()[2])
            sys.exit(-1)
        finally:
            _cf.close()

    '''
    attributes access methods
    '''
    def get_name(self):
        """
        Calibration name is read from the calibration file (field : CALIB_NAME).
        """
        return self._calib_name

    def get_calib_type(self):
        """
        Returns calibration type read from calibration file (field : CALIB_TYPE).
        Can be TABLE or POLY.
        """
        return self._calib_type

    def method(self):
        """
        Returns fitting method.
        arg in : void
        arg out : string : 'INTERPOLATION' | 'POLYFIT'
        """
        return self._method

    def set_method(self, method):
        self._method = method

    def get_fit_order(self):
        """
        Returns fit order for TABLE calibrations fitting.
        """
        return self._fit_order

    def set_fit_order(self, order):
        if isinstance(order, int):
            self._fit_order = order
        else:
            log.error("set_fit_order : <order> must be an int.")

    def get_calib_order(self):
        """
        Returns order of polynomia used to define calibration.
        Read from POLY calibration file (field : CALIB_ORDER).
        arg in : void
        arg out : int
        """
        print "calib_order=", self._calib_order
        return self._calib_order

    def set_calib_order(self, order):
        if isinstance(order, int):
            self._calib_order = order
        else:
            log.error("set_calib_order : <order> must be an int.")

    '''
    Calibration loading methods
    '''
    def load_calib(self, calib_file):
        _x_min =  float('inf')
        _x_max = -float('inf')
        _y_min =  float('inf')
        _y_max = -float('inf')
        _nb_points = 0
        xvalues = []
        yvalues = []
        _ligne_nb = 0
        _part_letter = "H"

        try:
            for raw_line in calib_file:
                _ligne_nb = _ligne_nb + 1

                # Removes optional starting "whitespace" characters :
                # string.whitespace -> '\t\n\x0b\x0c\r '
                line = raw_line.lstrip()

                # Line empty or full of space(s).
                if len(line) == 0:
                    log.debug("line %4d%s : empty" % (_ligne_nb, _part_letter))
                    continue

                # Commented line
                if line[0] == "#":
                    log.debug("line %4d%s : comment    : {%s}" % (_ligne_nb, _part_letter, line.rstrip()))
                    continue

                # Matches lines like :
                # CALIB_xxxx = YYYY
                matchCalibInfo = re.search(r'CALIB_(\w+)(?: )*=(?: )*(.+)', line)
                if matchCalibInfo:
                    _info  = matchCalibInfo.group(1)
                    _value = matchCalibInfo.group(2)

                    log.debug("line %4d%s : calib info : %30s   info={%s} value={%s}" % \
                              (_ligne_nb, _part_letter, matchCalibInfo.group(), _info, _value) )

                    if _info == "NAME":
                        self._calib_name = _value
                    elif _info == "TYPE":
                        self._calib_type = _value
                    elif _info == "TIME":
                        pass
                    elif _info == "ORDER":
                        self.set_calib_order(int(_value))
                        self.coeffs = numpy.linspace(0, 0, self.get_calib_order() + 1)
                    elif _info == "XMIN":
                        self.Xmin = float(_value)
                    elif _info == "XMAX":
                        self.Xmax = float(_value)
                    else:
                        _msg = "Parsing Error : unknown calib info {%s} with value {%s} at line %d" % \
                               (_info, _value, _ligne_nb)
                        raise XCalibError(_msg)

                else:
                    '''
                    Read DATA line.
                    '''
                    if self.get_calib_type() == "TABLE":
                        # Matches lines like  U35M[13.000000]=15.941000
                        # name of the calib must be known.
                        if self.get_name() is None:
                            raise XCalibError("Parsing Error : Line : %d : name of the calibration unknown." % _ligne_nb)
                        else:
                            matchPoint = re.search(r'%s\[(.+)\](?: )*=(?: )*(.+)' % self.get_name(), line)

                        if matchPoint:
                            # At least one ligne of the calib data has been read
                            # -> no more in header.
                            _part_letter = "D"

                            _xval = float(matchPoint.group(1))
                            _yval = float(matchPoint.group(2))
                            log.debug("line %4d%s : raw calib  : %30s   xval=%8g yval=%8g" % \
                                      (_ligne_nb, _part_letter, matchPoint.group(), _xval, _yval) )
                            _nb_points = _nb_points + 1

                            xvalues.append(_xval)
                            yvalues.append(_yval)

                            _x_min = min(_xval, _x_min)
                            _x_max = max(_xval, _x_max)
                            _y_min = min(_yval, _y_min)
                            _y_max = max(_yval, _y_max)

                        else:
                            log.debug("line %4d%s : nomatch    : {%s}" % (_ligne_nb, _part_letter, line.rstrip()))

                    elif self.get_calib_type() == "POLY":
                        # Matches lines like :
                        # C0 = 28.78
                        matchCoef = re.search(r'\s*C(\d+)\s*=\s*([-+]?\d*\.\d+|\d+)', line, re.M | re.I)
                        if matchCoef:
                            _coef = int(matchCoef.group(1))
                            _value = float(matchCoef.group(2))

                            log.debug("line %4d%s : raw calib  : %15s   coef=%8g value=%8g" % \
                                      (_ligne_nb, _part_letter, matchCoef.group(), _coef, _value) )

                            _pos = self.get_calib_order() - _coef
                            # print "_pos=", _pos
                            self.coeffs[_pos] = _value

                    else:
                        raise XCalibError("invalid calib type : %s" % self.get_calib_type())

            # End of parsing of lines.
            if self.get_calib_type() == "POLY":
                print "coefficients of the POLY:", self.coeffs

        except XCalibError:
            print "Error in parsing :"
            print sys.exc_info()[1]

            #import traceback
            #traceback.print_exc()
            sys.exit(0)

        if self.get_calib_type() == "TABLE":
            self.nb_calib_points = _nb_points
            self.Xmin = _x_min
            self.Xmax = _x_max
            self.Ymin = _y_min
            self.Ymax = _y_max
            log.info("Xcalibu : Ymin = %g  Ymax = %g  Nb points=%d" % (self.Ymin, self.Ymax, _nb_points))

        log.info("Xcalibu : Xmin = %g  Xmax = %g  Nb points=%d" % (self.Xmin, self.Xmax, _nb_points))

        self.x_raw = numpy.array(xvalues)
        self.y_raw = numpy.array(yvalues)

        log.debug("Raw X data : %s" % ", ".join(map(str, self.x_raw)))
        log.debug("Raw Y data : %s" % ", ".join(map(str, self.y_raw)))


    def fit(self):

        if self.method() != "POLYFIT":
            print "hummm : fit not needed... (method=%s)" % self.method()
            # print type(self.method())
        _order = self.get_fit_order()
        self.coeffs = None
        self.coeffR = None

        _time0 = time.time()

        # Fits direct conversion.
        self.coeffs = numpy.polyfit(self.x_raw, self.y_raw, _order)
        log.info("Xcalibu - Fitting took %g seconds" % (time.time() - _time0))
        log.info("Xcalibu - polynom coeffs = %s" % ",".join(map(str, self.coeffs)))

        self.x_fitted = numpy.linspace(self.Xmin, self.Xmax, 50)
        self.y_fitted = numpy.linspace(-100, 100, 50)
        self.y_fitted = map(self.calc_poly_value, self.x_fitted)

        # Fits reciproque conversion.
        self.coeffR = numpy.polyfit(self.y_raw, self.x_raw, _order)

        self.x_fittedR = numpy.linspace(self.Ymin, self.Ymax, 50)
        self.y_fittedR = numpy.linspace(-100, 100, 50)
        self.y_fittedR = map(self.calc_fitted_reverse_value, self.x_fittedR)

    def get_raw_x(self):
        return self.x_raw

    def get_raw_y(self):
        return self.y_raw

    """
    Returns the Y value for a given X calculated using the polynom
    coefficients stored in self.coeffs list.
    Used for fitting polynoms and for POLY calibrations.
    """
    def calc_poly_value(self, x):
        y = 0
        if self.get_calib_type() == "POLY":
            _order = self.get_calib_order()
        elif self.get_calib_type() == "TABLE":
            _order = self.get_fit_order()
        else:
            print "calc_poly_value : ERROR in calib type"

        for ii in range(_order + 1):
            y = y + self.coeffs[_order - ii] * pow(x, ii)

        return y

    def calc_fitted_reverse_value(self, y):
        x = 0

        if self.get_calib_type() == "POLY":
            _order = self.get_calib_order()
        elif self.get_calib_type() == "TABLE":
            _order = self.get_fit_order()
        else:
            print "calc_fitted_reverse_value : ERROR in calib type"

        #print "y=",y
        for ii in range(_order + 1):
            #print "_order=%d, ii=%d  " % (_order, ii)
            x = x + self.coeffR[_order - ii] * pow(y, ii)

        return x

    """
    Returns Y value interpolated from 2 points.
    For now only linear interpolation.
    """
    def calc_interpolated_value(self, x):

        try:
            # Search if there is a matching point.
            idx = numpy.where(self.x_raw == x)[0][0]
            return self.y_raw[idx]
        except IndexError:
            # Search next point
            idx = numpy.searchsorted(self.x_raw, x, side='left')
            x1 = self.x_raw[idx]
            x0 = self.x_raw[idx - 1]

            y0 = self.y_raw[idx - 1]
            y1 = self.y_raw[idx]

            y = y0 + (x - x0) * ((y1 - y0) / (x1 - x0))

            return y

    def plot(self):
        log.info("Plotting")

        if self.get_calib_type() == "POLY":
            self.x_calc = numpy.linspace(self.Xmin, self.Xmax, 50)
            self.y_calc = numpy.linspace(-100, 100, 50)
            self.y_calc = map(self.calc_poly_value, self.x_calc)


            print self.x_calc
            print self.y_calc
            plt.plot(self.x_calc, self.y_calc, 'o')
            plt.legend(['calculated curve'], loc='best')
            plt.show()

        if self.get_calib_type() == "TABLE":
            if self.method() == "POLYFIT":
                plt.plot(self.x_raw, self.y_raw, 'o', self.x_fitted, self.y_fitted, '4')
                plt.legend(['raw data(%s)' % self.get_name(), 'fit(order=%s)' % self.get_fit_order()], loc='best')
                plt.show()
            elif self.method() == "INTERPOLATION":
                p2 = plt.plot(self.x_raw, self.y_raw, 'o', linestyle='-')
                plt.legend([p2], ["data"], loc='best')
                plt.show()
            else:
                log.error("plot : Unknown method : %s" % self.method())

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

    def is_in_valid_x_range(self, x):

        if self.get_calib_type() == "POLY":
            return True

        if (x < self.Xmin) or (x > self.Xmax):
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

        if (y < self.Ymin) or (y > self.Ymax):
            log.info("Ymin=%f Ymax=%f" % (self.Ymin, self.Ymax))
            return False
        else:
            return True

    """
    Values readout
    """
    def get_y(self, x):
        log.debug("Xcalibu - %s - get y of %f" % (self.get_name(), x))

        if self.is_in_valid_x_range(x):
            if self.get_calib_type() == "TABLE":
                if self.method() == "POLYFIT":
                    y = self.calc_poly_value(x)
                elif self.method() == "INTERPOLATION":
                    y = self.calc_interpolated_value(x)
                else:
                    log.error("Unknown or not available reconstruction method : %s" %
                              self.method())
            elif self.get_calib_type() == "POLY":
                y = self.calc_poly_value(x)
            else:
                log.error("Unknown calibration type: %s" % self.get_calib_type())

            log.debug("y=%f" % y)
            return(y)
        else:
            log.error("Xcalibu - Error : x=%f is not in valid range for this calibration" % x)
            raise XCalibError("XValue %g out of limits [%g;%g]"%(x, self.Xmin, self.Xmax))

    def get_x(self, y):
        """
        Reciprocal calibration.
        """
        log.debug("Xcalibu - %s - get x of %f" % (self.get_name(), y))

        # Check validity range
        if self.is_in_valid_y_range(y):
            # order 3 poly calcul.
            # TODO : any order ....
            x = self.calc_fitted_reverse_value(y)
            log.debug("x=%f" % x)
            return(x)
        else:
            # raise XCalibError("YValue out of limits [%g;%g]"%(self.Ymin,self.Ymax))
            log.error("Xcalibu - Error : y=%f is not in valid range for this R calibration" % y)
            return (-1)



def demo(do_plot):

    """
    Demonstrations
    """
    myCalib1 = Xcalibu("POLY", "./examples/xcalibu_calib_poly.calib", "POLY")
    log.info("Xcalibu - TEST - Gap for %f keV : %f" % (5, myCalib1.get_y(5)))

    myCalib2 = Xcalibu("U32BC1G",
                       calib_file_name = "./examples/xcalibu_calib_table_undu.calib",
                       order = 2,
                       method = "POLYFIT")
    myCalib2.fit()
    log.info("Xcalibu - TEST - Gap for %f keV : %f" % (5, myCalib2.get_y(5)))

    myCalib3 = Xcalibu("B52", "./examples/xcalibu_calib_table.calib", "TABLE", 2, "INTERPOLATION")
    log.info("Xcalibu - TEST - Gap for %f keV : %f" % (1, myCalib3.get_y(1)))
    log.info("Xcalibu - TEST - Gap for %f keV : %f" % (2, myCalib3.get_y(2)))
    log.info("Xcalibu - TEST - Gap for %f keV : %f" % (4, myCalib3.get_y(4)))
    log.info("Xcalibu - TEST - Gap for %f keV : %f" % (9, myCalib3.get_y(9)))
    # errors :
    log.info("Xcalibu - TEST - Gap for %f keV : %f" % (0.5, myCalib3.get_y(0.5)))
    log.info("Xcalibu - TEST - Gap for %f keV : %f" % (12, myCalib3.get_y(12)))

    myCalibRingTx = Xcalibu("HPZ_RING_TX",
                       calib_file_name = "./examples/hpz_ring_Tx.calib",
                       calib_type = "TABLE",
                       order = 5,
                       method = "POLYFIT")
    myCalibRingTx.fit()

    myCalibRingTy = Xcalibu("HPZ_RING_TY",
                       calib_file_name = "./examples/hpz_ring_Ty.calib",
                       calib_type = "TABLE",
                       order = 4,
                       method = "POLYFIT")
    myCalibRingTy.fit()

    myCalibRingTz = Xcalibu("HPZ_RING_TZ",
                       calib_file_name = "./examples/hpz_ring_Tz.calib",
                       calib_type = "TABLE",
                       order = 20,
                       method = "POLYFIT")
    myCalibRingTz.fit()

    myCalibRingRx = Xcalibu("HPZ_RING_RX",
                       calib_file_name = "./examples/hpz_ring_Rx.calib",
                       calib_type = "TABLE",
                       order = 5,
                       method = "POLYFIT")
    myCalibRingRx.fit()

    myCalibRingRy = Xcalibu("HPZ_RING_RY",
                    calib_file_name ="./examples/hpz_ring_Ry.calib",
                    calib_type="TABLE",
                    order = 5,
                    method="POLYFIT")
    myCalibRingRy.fit()

    if do_plot:
        # myCalib1.plot()
        # myCalib2.plot()
        # myCalib3.plot()
        # myCalibRingTx.plot()
        myCalibRingTy.plot()
        # myCalibRingTz.plot()
        # myCalibRingRx.plot()
        # myCalibRingRy.plot()



def main(args):
    """
    Function main provided for demonstration and testing purposes.
    """
    print "--------------------{ Xcalibu }----------------------------------"

    """
    arguments parsing
    """
    from optparse import OptionParser
    parser = OptionParser('xcalibu.py')
    parser.add_option('-d', '--debug', type='string',
                      help="Available levels are :\n CRITICAL(50)\n \
                      ERROR(40)\n WARNING(30)\n INFO(20)\n DEBUG(10)",
                      default='INFO')

    parser.add_option('-p', '--plot', action="store_true", dest="plot", default=False,
                  help="Plots calibration")


    # Gathers options and arguments.
    (options, args) = parser.parse_args()
    # print options
    # print args

    """
    Log level
    """
    try:
        loglevel = getattr(logging, options.debug.upper())
    except AttributeError:
        # print "AttributeError  o.d=",options.debug
        loglevel = {50: logging.CRITICAL,
                    40: logging.ERROR,
                    30: logging.WARNING,
                    20: logging.INFO,
                    10: logging.DEBUG,
                    }[int(options.debug)]

    print "Xcalibu - log level = %s (%d)" % (logging.getLevelName(loglevel), loglevel)
    logging.basicConfig(format=LOG_FORMAT, level=loglevel)


    if len(args) == 0:
        print "no arg file -> launch default demo"
        demo(options.plot)
    else:
        _calib_file = args[0]
        print "use \"%s\" argument as calib test file" % _calib_file

        # new way to load calibrations.
        myCalib = Xcalibu( calib_file_name = _calib_file,
                           fit_order = 6,
                           method = "POLYFIT")

        if myCalib.get_calib_type() == "TABLE":
            myCalib.fit()

        if options.plot:
            myCalib.plot()




if __name__ == "__main__":
    main(sys.argv)
