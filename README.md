# Xcalibu

author: Cyril Guilloud ESRF BCU 2013-2023

Xcalibu is a python library to manage calibrations tables or polynomia.
It includes a PyTango device server in order to optionaly run it as a server.

xcalibu.py : python library
Xcalibuds.py : PyTango device server

Xcalibu name comes from the first use of this library to deal with undulators calibrations at ESRF.

* https://en.wikipedia.org/wiki/Undulator
* https://en.wikipedia.org/wiki/European_Synchrotron_Radiation_Facility

## installation

Available on PyPi or anaconda.org

## usage

to plot: `./xcalibu.py -p`

to debug:`./xcalibu.py -d10`

plot a file:`./xcalibu.py -p examples/xcalibu_calib_poly.calib`


## Examples

### TABLE + INTERPOL
```python
import numpy
import xcalibu
calib = xcalibu.Xcalibu()
calib.set_calib_file_name("mycalib.calib")
calib.set_calib_type("TABLE")
calib.set_reconstruction_method("INTERPOLATION")
calib.set_calib_time("1234.5678")
calib.set_calib_name("CAL")
calib.set_calib_description("dynamic calibration created for demo")
calib.set_raw_x(numpy.linspace(1, 10, 10))
calib.set_raw_y(numpy.array([3, 6, 5, 4, 2, 5, 7, 3, 7, 4]))
calib.plot()
calib.save()  # create a file named `mycalib.calib` in your current directory.
```

### TABLE + POLYFIT
```python
import numpy
import xcalibu
calib = xcalibu.Xcalibu()
calib.set_calib_file_name("mycalib.calib")
calib.set_calib_type("TABLE")
calib.set_reconstruction_method("POLYFIT")
calib.set_calib_time("1234.5678")
calib.set_calib_name("CAL")
calib.set_calib_description("dynamic calibration created for demo")
calib.set_raw_x(numpy.linspace(1, 10, 15))
calib.set_raw_y(numpy.array([4.1, 3.5, 3.6, 4.2, 4.5, 4, 3.9, 3.8, 4.5, 4.6, 6, 6.2, 4.7, 5, 4]))
calib.set_fit_order(6)
calib.fit()
calib.plot()
```


### POLY
```python

```




```
% cat mycalib.calib
# XCALIBU CALIBRATION

CALIB_NAME=CAL
CALIB_TYPE=TABLE
CALIB_TIME=1234.5678
CALIB_DESC=dynamic calibration created for demo

CAL[1.000000] = 3.000000
CAL[2.000000] = 6.000000
CAL[3.000000] = 5.000000
CAL[4.000000] = 4.000000
CAL[5.000000] = 2.000000
CAL[6.000000] = 5.000000
CAL[7.000000] = 7.000000
CAL[8.000000] = 3.000000
CAL[9.000000] = 7.000000
CAL[10.000000] = 4.000000
```

## command line usage

Options:
  -h: help
  -p: plot
  -d: debug


  -t type
  -r reconstruction_method
  -k kind of interpolation
  -n name

example:
  ./xcalibu.py -n calinou -t TABLE -r INTERPOLATION -k cubic examples/U32a_1_table.dat -p



