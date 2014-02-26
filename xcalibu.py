#!/usr/bin/env python
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

__author__ = "cyril.guilloud@esrf.fr"
__date__   = "2012 - 2013"

# imports python
import sys
import numpy
import time
import re
import matplotlib.pyplot as plt


# logging
import logging
log = logging.getLogger("XCALIBU")
LOG_FORMAT='%(name)s - %(levelname)s - %(message)s'


class XCalibError(Exception):
    '''Custom exception class for Xcalibu.'''
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return "XCALIBU error: %s"%self.message


class Xcalibu:
    calib_name = None
    Xmin = 0
    Xmax = 0
    Ymin = 0
    Ymax = 0
    x = None
    y = None
    _calib_type = None
    _method = None
    _order = None

    def __init__(self, calib_name, calib_file=None, calib_type=None, order=None, method=None):
        log.info("new xcalibration named %s"%calib_name)

        # Name of the calibration.
        self.calib_name = calib_name

        # Calibration type : TABLE or POLY.
        if calib_type:
            self._calib_type = calib_type

        # Order of the reconstruction method for TABLE calibrations.
        # or
        # Order of the polynom for POLY calibrations.
        if order:
            self._order = order

        # Reconstruction method for TABLE calibrations.
        # *INTERPOLATION : interpolation segment by segment.
        # or
        # *POLYFIT : polynomial fitting of dataset.
        if method:
            self._method = method

        # Calibration file.
        if calib_file:
            self.load_calibration_from_file(calib_file)

    def name(self):
        return self.calib_name

    def calib_type(self):
        return self._calib_type

    '''
    method
    '''
    def method(self):
        return self._method

    def set_method(self, method):
        self._method = method

    '''
    order
    '''
    def order(self):
        return self._order

    def set_order(self, order):
        if isinstance( order, int):
            self._order = order
        else:
            log.error("set_order : <order> must be an int.")


    def load_calibration_from_file(self, calib_file_name):

        try:
            _cf = open(calib_file_name, mode='r')
        except IOError:
            log.critical("Xcalibu : Unable to open file %s \n"%calib_file_name)
            exit()

        try:
            if self.calib_type() == "TABLE":
                self.load_table_calib(_cf)
            elif self.calib_type() == "POLY":
                self.load_poly_calibration(_cf)
            else:
                log.error("Calibration type error : %s \n"%self.calib_type())
            _cf.close()
        except:
            _cf.close()

    def load_table_calib(self, calib_file):
        _x_min = float('inf')
        _x_max = -1   # humm on gere que des val positives ???
        _y_min = float('inf')
        _y_max = -1
        _nb_points = 0
        xvalues = []
        yvalues = []


        for line in calib_file:
            # Matches lines like :
            # U35M[13.000000]=15.941000
            matchObj = re.search( r'%s\[(.+)\]=(.+)'%self.name(), line, re.M|re.I)

            if matchObj:
                log.debug("raw line : %s"%matchObj.group())
                _xval = float(matchObj.group(1))
                _yval = float(matchObj.group(2))
                log.debug("xval : %f   yval : %f"%(_xval, _yval))
                _nb_points = _nb_points + 1

                xvalues.append(_xval)
                yvalues.append(_yval)

                _x_min = min(_xval, _x_min)
                _x_max = max(_xval, _x_max)
                _y_min = min(_yval, _y_min)
                _y_max = max(_yval, _y_max)
            else:
                log.debug("nomatch : %s"%line)

        log.info("Xcalibu - Xmin = %g  Xmax = %g  Nb points=%d"%(_x_min, _x_max, _nb_points))

        self.nb_calib_points = _nb_points
        self.Xmin = _x_min
        self.Xmax = _x_max
        self.Ymin = _y_min
        self.Ymax = _y_max

        self.x_raw = numpy.array(xvalues)
        self.y_raw = numpy.array(yvalues)

        log.debug("Raw X data : %s"%", ".join(map(str, self.x_raw)))
        log.debug("Raw Y data : %s"%", ".join(map(str, self.y_raw)))

    def load_poly_calibration(self, calib_file):

        for line in calib_file:
            # Matches lines like :
            # ORDER = 2
            matchObj = re.search( r'\s*ORDER\s*=\s*(\d+)', line, re.M|re.I)

            if matchObj:
                _order = int(matchObj.group(1))
                print "found order : %d"%_order
                self.set_order(_order)
                self.coeff = numpy.linspace(0,0, _order+1)


            # Matches lines like :
            # XMIN = 2
            matchObj = re.search( r'\s*XMIN\s*=\s*([-+]?\d*\.\d+|\d+)', line, re.M|re.I)
            if matchObj:
                _xmin = float(matchObj.group(1))
                print "found xmin : %g"%_xmin
                self.Xmin = _xmin



            # Matches lines like :
            # XMAX = 15
            matchObj = re.search( r'\s*XMAX\s*=\s*([-+]?\d*\.\d+|\d+)', line, re.M|re.I)
            if matchObj:
                _xmax = float(matchObj.group(1))
                print "found xmax : %g"%_xmax
                self.Xmax = _xmax


            # Matches lines like :
            # C0 = 28.78
            matchObj = re.search( r'\s*C(\d+)\s*=\s*([-+]?\d*\.\d+|\d+)', line, re.M|re.I)
            if matchObj:
                _coef  = int(matchObj.group(1))
                _value = float(matchObj.group(2))
                print "found C%d : %g"%(_coef, _value)
                _pos = self.order() - _coef
                self.coeff[_pos] = _value

        print "coefs:",self.coeff


    def fit(self):

        if self.method() is not "POLYFIT":
            print "hummm : fit not needed..."

        _order = self.order()
        self.coeff  = None
        self.coeffR = None

        _time0 = time.time()

        # Fits direct conversion.
        self.coeff = numpy.polyfit(self.x_raw, self.y_raw, _order)
        log.info("Xcalibu - Fitting took %g seconds"%(time.time()-_time0))
        log.info("Xcalibu - polynom coeff = %s"%",".join(map(str,self.coeff)))

        self.x_fitted = numpy.linspace(self.Xmin, self.Xmax, 50)
        self.y_fitted = numpy.linspace(-100, 100, 50)
        self.y_fitted = map(self.calc_poly_value, self.x_fitted)

        # Fits reciproque conversion.
        self.coeffR = numpy.polyfit(self.y_raw, self.x_raw, _order)

        self.x_fittedR = numpy.linspace(self.Ymin, self.Ymax, 50)
        self.y_fittedR = numpy.linspace(-100, 100, 50)
        self.y_fittedR = map(self.calc_fitted_reverse_value, self.x_fittedR)

    '''
    Returns the Y value for a given X calculated using the polynom
    coefficients stored in self.coeff list.
    Used for fitting polynoms and for POLY calibrations.
    '''
    def calc_poly_value(self, x):
        y = 0
        _order = self.order()
        for ii in range(_order+1):
            y = y + self.coeff[_order-ii]*pow(x, ii)

        return y

    def calc_fitted_reverse_value(self, y):
        x = 0
        _order = self.order()
        #print "y=",y
        for ii in range(_order+1):
            #print "_order=%d, ii=%d  "%(_order, ii)
            x = x + self.coeffR[_order-ii]*pow(y, ii)

        return x

    '''
    Returns Y value interpolated from 2 points.
    For now only linear interpolation.
    '''
    def calc_interpolated_value(self, x):

        try:
            # Search if there is a matching point.
            idx = numpy.where(self.x_raw==x)[0][0]
            return self.y_raw[idx]
        except IndexError:
            # Search next point
            idx = numpy.searchsorted(self.x_raw, x, side='left')
            x1 = self.x_raw[idx]
            x0 = self.x_raw[idx-1]

            y0 = self.y_raw[idx-1]
            y1 = self.y_raw[idx]

            y = y0 + (x - x0)*((y1-y0)/(x1-x0))

            return y


    def plot(self):
        log.info("Plotting")

        if self.calib_type() == "POLY":
            self.x_calc = numpy.linspace(self.Xmin, self.Xmax, 50)
            self.y_calc = numpy.linspace(-100, 100, 50)
            self.y_calc = map(self.calc_poly_value, self.x_calc)

            plt.plot(self.x_calc, self.y_calc, 'o')
            plt.legend(['calculated curve'], loc='best')
            plt.show()

        if self.calib_type() == "TABLE":
            if self.method() == "POLYFIT":
                plt.plot(self.x_raw, self.y_raw, 'o', self.x_fitted, self.y_fitted,'4')
                plt.legend(['raw data','fit'], loc='best')
                plt.show()
            elif self.method() == "INTERPOLATION":
                p2 = plt.plot(self.x_raw, self.y_raw, 'o', linestyle='-')
                plt.legend([p2], ["data"], loc='best')
                plt.show()
            else:
                log.error("plot : Unknown method : %s"%self.method())


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

        if self.calib_type() == "POLY":
            return True

        if (x < self.Xmin) or (x>self.Xmax):
            log.info("Xmin=%f Xmax=%f"%(self.Xmin, self.Xmax))
            return False
        else:
            return True

    def is_in_valid_y_range(self, y):

        # humm bad : would be better to define Ymin Ymax as bounds of
        # a monoton portion of the poly...
        # but how ???
        if self.calib_type() == "POLY":
            return True

        if (y < self.Ymin) or (y>self.Ymax):
            log.info("Ymin=%f Ymax=%f"%(self.Ymin, self.Ymax))
            return False
        else:
            return True


    """
    Values readout
    """
    def get_y(self, x):
        log.debug("Xcalibu - %s - get y of %f"%(self.name(), x))

        if self.is_in_valid_x_range(x):
            if self.calib_type() == "TABLE":
                if self.method() == "POLYFIT":
                    y = self.calc_poly_value(x)
                elif self.method() == "INTERPOLATION":
                    y = self.calc_interpolated_value(x)
                else:
                    log.error("Unknown or not available reconstruction method : %s"%
                              self.method())
            elif self.calib_type() == "POLY":
                y = self.calc_poly_value(x)
            else:
                log.error("Unknown calibration type: %s"%self.calib_type())

            log.debug("y=%f"%y)
            return(y)
        else:
            # raise XCalibError("XValue out of limits [%g;%g]"%(self.Xmin,self.Xmax))
            log.error("Xcalibu - Error : x=%f is not in valid range for this calibration"%x)
            return (-1)


    def get_x(self, y):
        '''
        Reciprocal calibration.
        '''
        log.debug("Xcalibu - %s - get x of %f"%(self.name(), y))

        # Check validity range
        if self.is_in_valid_y_range(y):
            # order 3 poly calcul.
            # TODO : any order ....
            x = self.calc_fitted_reverse_value(y)
            log.debug("x=%f"%x)
            return(x)
        else:
            # raise XCalibError("YValue out of limits [%g;%g]"%(self.Ymin,self.Ymax))
            log.error("Xcalibu - Error : y=%f is not in valid range for this R calibration"%y)
            return (-1)





def main(args):
    """
    Function main provided for demonstration and testing purposes.
    """

    print "--------------------{ Xcalibu }----------------------------------"

    from optparse import OptionParser
    parser = OptionParser('xcalibu.py')
    parser.add_option('-d','--debug', type='string',
                      help="Available levels are :\n CRITICAL(50)\n ERROR(40)\n WARNING(30)\n INFO(20)\n DEBUG(10)", 
                      default='INFO')
    parser.add_option('-p','--printtostdout', action='store_true', default=False,
                      help='Print all log messages to stdout')
    options,args = parser.parse_args()

    try:
        loglevel = getattr(logging, options.debug.upper())
    except AttributeError:
        # print "AttributeError  o.d=",options.debug
        loglevel = {50:logging.CRITICAL,
                    40:logging.ERROR,
                    30:logging.WARNING,
                    20:logging.INFO,
                    10:logging.DEBUG,
                    }[int(options.debug)]

    print "Xcalibu - log level = %s (%d)"%(logging.getLevelName(loglevel), loglevel)
    logging.basicConfig(format=LOG_FORMAT, level=loglevel)


    """
    Demonstrations
    """

    myCalib1 = Xcalibu("POLY", "./examples/xcalibu_calib_poly.calib", "POLY")
    log.info("Xcalibu - TEST - Gap for %f keV : %f"%(5, myCalib1.get_y(5)))


    myCalib2 = Xcalibu("U32BC1G",
                       calib_file = "./examples/xcalibu_calib_table_undu.calib",
                       calib_type = "TABLE",
                       order      = 2,
                       method     = "POLYFIT")
    myCalib2.fit()
    log.info("Xcalibu - TEST - Gap for %f keV : %f"%(5, myCalib2.get_y(5)))



    myCalib3 = Xcalibu("B52", "./examples/xcalibu_calib_table.calib", "TABLE", 2, "INTERPOLATION")
    log.info("Xcalibu - TEST - Gap for %f keV : %f"%(1, myCalib3.get_y(1)))
    log.info("Xcalibu - TEST - Gap for %f keV : %f"%(2, myCalib3.get_y(2)))
    log.info("Xcalibu - TEST - Gap for %f keV : %f"%(4, myCalib3.get_y(4)))
    log.info("Xcalibu - TEST - Gap for %f keV : %f"%(9, myCalib3.get_y(9)))
    # errors :
    log.info("Xcalibu - TEST - Gap for %f keV : %f"%(0.5, myCalib3.get_y(0.5)))
    log.info("Xcalibu - TEST - Gap for %f keV : %f"%(12, myCalib3.get_y(12)))

#     #log.info("Xcalibu - TEST - Gap for %f keV : %f"%(3, myCalib.get_y(3)))
#     #log.info("Xcalibu - TEST - Gap for %f keV : %f"%(23, myCalib.get_y(23)))
#
#     """Tests of reciprocal calibration"""
#     log.info("Xcalibu - TEST - ene of %f mm gap : %f"%(18.389143, myCalib.get_x(18.389143)))
#
#     errors = numpy.linspace(myCalib.Xmin+1, myCalib.Xmax-1, 20)
#     print "Errors between the 2 calibrations (fit order=%d):"%myCalib.order()
#     _err_sum = 0
#
#     for ene in errors:
#         _err = myCalib.get_x(myCalib.get_y(ene)) - ene
#         _err_sum = _err_sum + abs(_err)
#         print "%.3g(%.4f%%) "%(_err, _err*100/ene),
#     print ""
#
#     print "SUM abs error:%g  avg:%g  (%d points)"%
#            (_err_sum, _err_sum/len(errors), len(errors))
#     print ""
#     print "fitted_val(7) =", myCalib.calc_poly_value(7)
#     print ""

    myCalib1.plot()

    #myCalib2.plot()

    #myCalib3.plot()


if __name__ == "__main__":
    main(sys.argv)


