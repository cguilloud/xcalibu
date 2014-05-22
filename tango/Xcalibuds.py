#!/usr/bin/env python
# -*- coding:utf-8 -*-

import PyTango
import traceback
import sys

from xcalibu import XCalibError
import xcalibu

import logging
log = logging.getLogger("Xcalibuds ")
LOG_FORMAT='%(name)s - %(levelname)s - %(message)s'

class Xcalibuds(PyTango.Device_4Impl):
    def __init__(self,cl, name):
        PyTango.Device_4Impl.__init__(self,cl,name)

        self.debug_stream("In __init__()")
        self.init_device()

    def delete_device(self):
        self.debug_stream("In delete_device()")

    def init_device(self):
        self.debug_stream("In init_device()")
        self.get_device_properties(self.get_device_class())

        self.attr_Xdata_read = [0.0]

        # From here we can get properties.

        # -v1
        self.info_stream( "INFO  STREAM ON +++++++++++++++++++++++++++++++++++++")
        self.warn_stream( "WARN  STREAM ON +++++++++++++++++++++++++++++++++++++")
        self.error_stream("ERROR STREAM ON +++++++++++++++++++++++++++++++++++++")
        self.fatal_stream("FATAL STREAM ON +++++++++++++++++++++++++++++++++++++")

        # -v4
        self.debug_stream("DEBUG STREAM ON +++++++++++++++++++++++++++++++++++++")

        # bof ?
        self.db = PyTango.Database()
        try:
            self.log_level  = int(self.db.get_class_property("Xcalibuds", "log_level")['log_level'][0])
        except:
            self.log_level  = 50
        self.info_stream("log_level set to %d"%self.log_level)

        # calibu logging
        logging.basicConfig(format=LOG_FORMAT, level=self.log_level)

        # Gets calibration file name from device properties
        self.calib_file_name  = self.device_property_list['file'][2]
        self.fit_order = int(self.device_property_list['fit_order'][2])
        self.fit_method = self.device_property_list['fit_method'][2][0]
        self.debug_stream("file to load = %s" % self.calib_file_name)
        self.debug_stream("fit_order = %d" % self.fit_order)
        self.debug_stream("fit_method = %s" % self.fit_method)

        # Loads a calibration.
        self.calib = xcalibu.Xcalibu( self.calib_file_name,
                                      self.fit_order,
                                      self.fit_method )

        if self.calib.get_calib_type() == "TABLE":
            self.info_stream("fits TABLE calib.")
            self.calib.fit()


    def always_executed_hook(self):
        self.debug_stream("In always_excuted_hook()")

    def dev_state(self):
        """ This command gets the device state (stored in its device_state
        data member) and returns it to the caller.

        :param : none
        :type: PyTango.DevVoid
        :return: Device state
        :rtype: PyTango.CmdArgType.DevState """
        self.debug_stream("In dev_state()")
        argout = PyTango.DevState.UNKNOWN


        self.set_state(PyTango.DevState.ON)


        if argout != PyTango.DevState.ALARM:
            PyTango.Device_4Impl.dev_state(self)
        return self.get_state()


    def read_Xmin(self, attr):
        self.debug_stream("In read_Xmin()")
        attr.set_value(self.calib.min_x())

    def read_Xmax(self, attr):
        self.debug_stream("In read_Xmax()")
        attr.set_value(self.calib.max_x())

    def read_Ymin(self, attr):
        self.debug_stream("In read_Ymin()")
        attr.set_value(self.calib.min_y())

    def read_Ymax(self, attr):
        self.debug_stream("In read_Ymax()")
        attr.set_value(self.calib.max_y())

    def read_calib_order(self, attr):
        self.debug_stream("In read_calib_order()")
        try:
            attr.set_value(self.calib.get_calib_order())
        except:
            import traceback
            traceback.print_exc()

    def read_calib_type(self, attr):
        self.debug_stream("In read_calib_type()")
        try:
            attr.set_value(self.calib.get_calib_type())
        except:
            import traceback
            traceback.print_exc()

    def read_calib_name(self, attr):
        self.debug_stream("In read_calib_name()")
        try:
            attr.set_value(self.calib.get_name())
        except:
            import traceback
            traceback.print_exc()

    def read_fit_order(self, attr):
        self.debug_stream("In read_fit_order()")
        try:
            attr.set_value(self.calib.get_fit_order())
        except:
            import traceback
            traceback.print_exc()

    def read_Xdata(self, attr):
        self.debug_stream("In read_Xdata()")
        attr.set_value(self.calib.get_raw_x())

    def write_Xdata(self, attr):
        self.debug_stream("In write_Xdata()")
        data=attr.get_write_value()


    def read_Ydata(self, attr):
        self.debug_stream("In read_Ydata()")
        attr.set_value(self.calib.get_raw_y())

    def write_Ydata(self, attr):
        self.debug_stream("In write_Ydata()")
        data=attr.get_write_value()





    def read_attr_hardware(self, data):
        self.debug_stream("In read_attr_hardware()")


    #-----------------------------------------------------------------------------
    #    Motor command methods
    #-----------------------------------------------------------------------------
    def On(self):
        """ Enable DS...

        :param :
        :type: PyTango.DevVoid
        :return:
        :rtype: PyTango.DevVoid """
        self.debug_stream("In On()")

    def get_y(self, argin):
        """ Returns the Y value of calibration corresponding to X argin.

        :param argin: X value
        :type: PyTango.DevFloat
        :return: Y value of the calibration if X in valid range.
        :rtype: PyTango.DevFloat """
        self.debug_stream("In get_y()")

        try:
            argout = self.calib.get_y(argin)
        except XCalibError:
            self.error_stream( str(sys.exc_info()[1]))
            argout = -666
            raise
        return argout

    def get_x(self, argin):
        """ Returns the X value of calibration corresponding to Y argin.

        :param argin: Y value
        :type: PyTango.DevFloat
        :return: X value of the calibration if Y in valid range and calibration is reversible
        :rtype: PyTango.DevFloat """
        self.debug_stream("In get_x()")

        argout = self.calib.get_x(argin)

        return argout


    def load_calibration(self, argin):
        """ Loads calibration.

        :param argin: path + filename
        :type: PyTango.DevString
        :return: None
        :rtype: PyTango.DevVoid """
        self.debug_stream("In load_calibration()")
        argout = [0]

        return argout


    def save_calibration(self, argin):
        """ Saves calibration.

        :param argin: path + filename
        :type: PyTango.DevString
        :return: None
        :rtype: PyTango.DevVoid """
        self.debug_stream("In save_calibration()")
        argout = [0]

        return argout



class XcalibudsClass(PyTango.DeviceClass):
    #    Class Properties
    class_property_list = {
        'log_level':
        [PyTango.DevShort, "log level for Xcalibu lib (in {10; 20; 30; 40; 50})",
         [50] ],
        }

    #    Device Properties
    device_property_list = {
        'file':
        [PyTango.DevString, "path+ filename of the calibration file",
         ["./tutu.calib"] ],
        'fit_order':
        [PyTango.DevShort, "order of the poly for TABLE calibration fitting",
         [2] ],
        'fit_method':
        [PyTango.DevString, "data reconstruction method : INTERPOLATION or POLYFIT",
         ["POLYFIT"] ],
        }

    #    Command definitions
    cmd_list = {
        'On':
            [[PyTango.DevVoid, "none"],
            [PyTango.DevVoid, "none"]],
        'get_y':
            [[PyTango.DevFloat, "x value"],
            [PyTango.DevFloat, "y value"]],
        'get_x':
            [[PyTango.DevFloat, "none"],
            [PyTango.DevFloat, "none"]],
        'load_calibration':
            [[PyTango.DevString, "path and filename of calibraiton to load"],
            [PyTango.DevVoid, "none"]],
        'save_calibration':
            [[PyTango.DevString, "path and filename of calibraiton to save"],
            [PyTango.DevVoid, "none"]],
        }


    #    Attribute definitions
    attr_list = {
        'Xmin':
            [[PyTango.DevFloat,
            PyTango.SCALAR,
            PyTango.READ],
            {
                'label': 'X min',
                'format': "%10.3f",
                'unit': " ",
                'description': "minimal valid X value of current calibration ",
            } ],
        'Xmax':
            [[PyTango.DevFloat,
            PyTango.SCALAR,
            PyTango.READ],
            {
                'format': "%10.3f",
                'unit': " ",
                'description': "maximal valid X value of current calibration ",
            } ],
        'Ymin':
            [[PyTango.DevFloat,
            PyTango.SCALAR,
            PyTango.READ],
            {
                'format': "%10.3f",
                'unit': " ",
                'description': "minimal valid Y value of current calibration ",
            } ],

        'Ymax':
            [[PyTango.DevFloat,
            PyTango.SCALAR,
            PyTango.READ],
            {
                'format': "%10.3f",
                'unit': " ",
                'description': "maximal valid Y value of current calibration ",
            } ],

        'calib_order':
            [[PyTango.DevShort,
            PyTango.SCALAR,
            PyTango.READ],
            {
                'format': "%d",
                'unit': " ",
                'description': "Order of the given calibration.",
            } ],

        'fit_order':
            [[PyTango.DevShort,
            PyTango.SCALAR,
            PyTango.READ],
            {
                'format': "%d",
                'unit': " ",
                'description': "Order of the polynomia to use to fit raw data.",
            } ],

        'calib_type':
            [[PyTango.DevString,
            PyTango.SCALAR,
            PyTango.READ],
            {
                'format': "%s",
                'unit': " ",
                'description': "Type of the given calibration : TABLE or POLY",
            } ],

        'calib_name':
            [[PyTango.DevString,
            PyTango.SCALAR,
            PyTango.READ],
            {
                'format': "%s",
                'unit': " ",
                'description': "Name of the calibration read from calib file",
            } ],

         'Xdata':
            [[PyTango.DevFloat,
            PyTango.SPECTRUM,
            PyTango.READ_WRITE, 2000],
            {
                'description': "X raw data",
            } ],

         'Ydata':
            [[PyTango.DevFloat,
            PyTango.SPECTRUM,
            PyTango.READ_WRITE, 2000],
            {
                'description': "Y raw data",
            } ],
        }

def main():

    try:
        py = PyTango.Util(sys.argv)
        py.add_class(XcalibudsClass, Xcalibuds, 'Xcalibuds')


        U = PyTango.Util.instance()
        U.server_init()
        U.server_run()


    except PyTango.DevFailed,e:
        print '-------> Received a DevFailed exception:',e
    except Exception,e:
        print '-------> An unforeseen exception occured....',e

if __name__ == '__main__':
    main()
