#!/usr/bin/python


import sys
import PyTango

_ds_name = sys.argv[1]

print "DS name =", _ds_name

dp = PyTango.DeviceProxy(_ds_name)

print "DS State is", dp.state()
print "Calib name = ", dp.calib_name
print " Xmin=%g" % dp.Xmin
print " Xmax=%g" % dp.Xmax

print " Ymin=%g" % dp.Ymin
print " Ymax=%g" % dp.Ymax

if dp.calib_type == "TABLE":
    print " fit order = %d" % dp.fit_order

if dp.calib_type == "POLY":
    print " calib order = %d" % dp.calib_order

print " f(3)=%g" % dp.get_y(3)
print " f(1)=%g" % dp.get_y(1)


try:
    print " f(666)=%g" % dp.get_y(666)
except:
    print " 666 is out of range"


# must return : -0.444837391376

