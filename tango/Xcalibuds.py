#!/usr/bin/env python
# -*- coding:utf-8 -*-

import PyTango
import traceback
import sys

import xcalibu

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

        # Gets calibration file name from device properties
        self.calib_file_name  = self.device_property_list['calibration_file'][2]
        print "Calibrtion file to load : %s" % self.calib_file_name

        # load a calibration
        self.calib = xcalibu.Xcalibu("POLY", self.calib_file_name, "POLY")

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


    def read_poly_order(self, attr):
        self.debug_stream("In read_poly_order()")
        attr.set_value(self.calib.order())



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
        argout = self.calib.get_y(argin)

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
        }

    #    Device Properties
    device_property_list = {
        'calibration_file':
        [PyTango.DevString,
         "path+ filename of the calibration file",
         ["./tutu.calib"] ],
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
        'poly_order':
            [[PyTango.DevShort,
            PyTango.SCALAR,
            PyTango.READ],
            {
                'format': "%d",
                'unit': " ",
                'description': "Order of the given calibration polynom.",
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
