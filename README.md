# Xcalibu

author: Cyril Guilloud ESRF BCU 2013-2019

Xcalibu is a python library to manage calibrations tables or polynomia.
It includes a PyTango device server in order to optionally run it as a server.

xcalibu.py : python library
Xcalibuds.py : PyTango device server

Xcalibu name comes from the first use of this library to calibrate undulators,
devices increasing X-ray flux on synchrotron's beamlines.

Curious reader can have look here:

* https://en.wikipedia.org/wiki/Undulator
* https://en.wikipedia.org/wiki/European_Synchrotron_Radiation_Facility

## installation

pip install xcalibu

## usage

to plot: `./xcalibu.py -p`

to debug:`./xcalibu.py -d10`

plot a file:`./xcalibu.py -p examples/xcalibu_calib_poly.calib`


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
calib.save()

```
This will create a file named `mycalib.calib` in your current directory.

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

That you can now use and plot for example:


```
% xcalibu ./mycalib.calib  -p

------------------------{ Xcalibu }----------------------------------
[xcalibu] - log level = INFO (20)
use "./mycalib.calib" argument as calib test file
XCALIBU - INFO - DATA lines read : 10
XCALIBU - INFO -  Ymin =          2  Ymax =          7  Nb points =   10
XCALIBU - INFO -  Xmin =          1  Xmax =         10  Nb points =   10
XCALIBU - INFO - TABLE + INTERPOLATION => NO FIT
XCALIBU - INFO - y value of 5.5 = 3.5 (3.361701965332031e-05)
XCALIBU - INFO - Calculation of 25 values of y. duration : 0.00021958351135253906
XCALIBU - INFO - Plotting

%

```
