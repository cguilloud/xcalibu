#!/usr/bin/env python
# -*- coding:utf-8 -*-
import xcalibu

import PyTango
import traceback
import sys


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


    def read_Steps_per_unit(self, attr):
        self.debug_stream("In read_Steps_per_unit()")
        attr.set_value(self.axis.steps_per_unit())

    def write_Steps_per_unit(self, attr):
        self.debug_stream("In write_Steps_per_unit()")
        data=attr.get_write_value()
        print "not implemented"



    def read_attr_hardware(self, data):
        self.debug_stream("In read_attr_hardware()")


    #-----------------------------------------------------------------------------
    #    Motor command methods
    #-----------------------------------------------------------------------------
    def On(self):
        """ Enable power on motor

        :param :
        :type: PyTango.DevVoid
        :return:
        :rtype: PyTango.DevVoid """
        self.debug_stream("In On()")

class XcalibudsClass(PyTango.DeviceClass):
    #    Class Properties
    class_property_list = {
        }

    #    Device Properties
    device_property_list = {
        }

    #    Command definitions
    cmd_list = {
        'On':
            [[PyTango.DevVoid, "none"],
            [PyTango.DevVoid, "none"]],
        }


    #    Attribute definitions
    attr_list = {
        'Steps':
            [[PyTango.DevDouble,
            PyTango.SCALAR,
           #PyTango.READ_WRITE],
            PyTango.READ],
            {
                'label': "Steps per mm",
                'unit': "steps/mm",
                'format': "%7.1f",
                'Display level': PyTango.DispLevel.EXPERT,
                #'Memorized':"true"
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
