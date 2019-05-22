#!/usr/bin/python

import PyTango

XDS = "id26/xcalibu/t26"

xdev = PyTango.DeviceProxy(XDS)

print("Info about %s" % XDS)
print("CALIB_DESCRIPTION =", xdev.calib_description)
print("CALIB_NAME =", xdev.calib_name)
print("CALIB_ORDER =", xdev.calib_order)
print("CALIB_TIME =", xdev.calib_time)

print("file_name =", xdev.file_name)
print("rec meth =", xdev.reconstruction_method)
print("xmin =", xdev.Xmin)
print("ymin =", xdev.Ymin)
print("xmax =", xdev.Xmax)
print("ymax =", xdev.Ymax)

print("dataset_size =", xdev.dataset_size)

print("")
print("------ save calibration in new file ------------")

_file_name = "/users/blissadm/dev/xcalibu/examples/tutu.calib"
xdev.file_name = _file_name
xdev.save_calibration()
