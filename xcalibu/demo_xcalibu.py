#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Examples of calibrations for test and demo purposes.
"""

import logging
import os
import numpy
from xcalibu import Xcalibu

XCALIBU_DIRBASE = os.path.dirname(os.path.realpath(__file__))

log = logging.getLogger("DEMO_XCALIBU")


# Some data for demo
demo_calib_string = """
# TEST calibration
# Type TABLE
# Comments are starting with '#'
# Spaces are mainly ignored.

CALIB_NAME = B52
CALIB_TYPE = TABLE
CALIB_TIME = 1400081171.300155
CALIB_DESC = 'test table : example of matching lines'
#CALIB_TITI = 14

B52[0.8e-2] = -0.83e-2
B52[1]=1
B52[3]= 2
B52[5]=-12
B52 [6]=  -3
B52 [7]=   2
B52[10]=   4.5
 B52[13]=7.5
   B52[15]=18.5
B52[18]=0.5e2
B52[23]=	42
B52[23.1]=0.61e2
B52[27.401] = 0.72e2
B52[32]=  62
B52[0.5e2] = +0.53e2
"""


def demo_xcalibu_1(do_plot):
    """
    string calibration
    """
    log = logging.getLogger("XCALIBU")

    # log.info("===== use: demo_calib_string str ; POLYFIT ; fit_order = 2 ===================\n")
    myCalibString = Xcalibu(
        calib_string=demo_calib_string, fit_order=2, reconstruction_method="POLYFIT"
    )
    log.info("TEST -         demo_calib_string(%f) = %f" % (5, myCalibString.get_y(5)))
    log.info("TEST - inverse_demo_calib_string(%f) = %f" % (4, myCalibString.get_x(4)))

    myCalibString.print_info()

    if do_plot:
        myCalibString.plot()


def demo_xcalibu_2(do_plot):
    """
    2nd order POLY calibration from file.
    """
    log = logging.getLogger("XCALIBU")

    myCalibPoly = Xcalibu(calib_file_name=XCALIBU_DIRBASE + "/examples/poly.calib")
    myCalibPoly.print_info()

    if do_plot:
        myCalibPoly.plot()


def demo_xcalibu_3(do_plot):
    """
    TABLE calibration from file with POLYFIT reconstruction method
    """
    log = logging.getLogger("XCALIBU")

    myCalib2 = Xcalibu(
        calib_file_name=XCALIBU_DIRBASE + "/examples/undu_table.calib",
        fit_order=2,
        reconstruction_method="POLYFIT",
    )
    log.info("TEST - Gap for %f keV : %f" % (5, myCalib2.get_y(5)))

    myCalib2.print_info()

    if do_plot:
        myCalib2.plot()


def demo_xcalibu_U32a(do_plot):
    """
    U32a undu table calibration.
    U32a_1_table.dat looks like:
        #E    u32a
        4.500 13.089
        4.662 13.410
        4.823 13.727
        ...
        10.444 34.814
        10.500 36.708
        10.675 41.711
    """
    log = logging.getLogger("XCALIBU")

    myCalibU32a = Xcalibu(calib_name="U32ATABLE", calib_type="TABLE",
                          calib_file_name=XCALIBU_DIRBASE + "/examples/U32a_1_table.txt",
                          description="2cols table calib of U32A undulator")
    # myCalibU32a.set_reconstruction_method("INTERPOLATION", kind="cubic")
    myCalibU32a.set_reconstruction_method("INTERPOLATION", kind="quadratic")

    myCalibU32a.set_x_limits(None, None)
    myCalibU32a.set_interpol_fill_value(numpy.nan)

    myCalibU32a.compute_interpolation()


    myCalibU32a.print_info()

    print(f"   myCalibU32a(-42) = {myCalibU32a.get_y(-42)}")
    print(f"   myCalibU32a(4.5) = {myCalibU32a.get_y(4.5)}")
    print(f"     myCalibU32a(7) = {myCalibU32a.get_y(7)}")
    print(f"myCalibU32a(10.675) = {myCalibU32a.get_y(10.675)}")
    print(f"   myCalibU32a(+42) = {myCalibU32a.get_y(+42)}")

#    print("get_x(get_y(7))=", myCalibU32a.get_x(float(myCalibU32a.get_y(7))))
    # quadratic -> 7.0000295
    #     cubic -> 6.9997924

#    print("get_x(get_y(7.04))=", myCalibU32a.get_x(float(myCalibU32a.get_y(7.04))))
    # quadratic -> 7.04
    #     cubic -> 7.039999

    myCalibU32a.print_info()
    if do_plot:
        myCalibU32a.plot()


def demo_xcalibu_table15(do_plot):
    """
    TABLE calibration examples/table.calib
    15 points table calib (legacy format B52[1]=1)
    """
    log = logging.getLogger("XCALIBU")

    myCalibTable = Xcalibu(
        calib_file_name=XCALIBU_DIRBASE + "/examples/table.calib",
        fit_order=2,
        reconstruction_method="INTERPOLATION",
    )
    log.info("TEST - Gap for %f keV : %f" % (1, myCalibTable.get_y(1)))
    log.info("TEST - Gap for %f keV : %f" % (2, myCalibTable.get_y(2)))
    log.info("TEST - Gap for %f keV : %f" % (4, myCalibTable.get_y(4)))
    log.info("TEST - Gap for %f keV : %f" % (9, myCalibTable.get_y(9)))
    # errors :
    #    log.info("TEST - Gap for %f keV : %f" % (0.5, myCalibTable.get_y(0.5)))
    #    log.info("TEST - Gap for %f keV : %f" % (12, myCalibTable.get_y(12)))
    #  myCalibTable.get_x(42)

    myCalibTable.print_info()

    if do_plot:
        myCalibTable.plot()


def demo_xcalibu_cubic(do_plot):
    """
    10 points table ~~ cubic func
    """
    log = logging.getLogger("XCALIBU")

    myCalibCubic = Xcalibu(
        calib_file_name=XCALIBU_DIRBASE + "/examples/cubic.calib",
        fit_order=3,
        reconstruction_method="POLYFIT",
    )

    myCalibCubic.print_info()

    if do_plot:
        myCalibCubic.plot()

def demo_xcalibu_RingRy(do_plot):
    """
    RingRy TABLE calibration 360 points
    """
    log = logging.getLogger("XCALIBU")


    myCalibRingRy = Xcalibu(
        calib_file_name=XCALIBU_DIRBASE + "/examples/hpz_ring_Ry.calib",
        fit_order=5,
        reconstruction_method="POLYFIT",
    )
    print("saving table demo....")
    myCalibRingRy.set_calib_file_name("ttt.calib")
    myCalibRingRy.save()

    myCalibRingRy.print_info()

    if do_plot:
        myCalibRingRy.plot()


def demo_xcalibu_dynamic(do_plot):
    """
    Dynamicaly populated calibration
    """
    log = logging.getLogger("XCALIBU")

    print("Example : creation of an empty TABLE calib then populate it with in-memory data")
    myDynamicCalib = Xcalibu()
    myDynamicCalib.set_calib_file_name("ddd.calib")
    myDynamicCalib.set_calib_name("DynCalTable")
    myDynamicCalib.set_calib_type("TABLE")
    myDynamicCalib.set_calib_time("1234.5678")
    myDynamicCalib.set_calib_description("dynamic calibration created for demo")
    myDynamicCalib.set_raw_x(numpy.linspace(1, 10, 10))
    myDynamicCalib.set_raw_y(numpy.array([3, 6, 5, 4, 2, 5, 7, 3, 7, 4]))
    myDynamicCalib.set_reconstruction_method("INTERPOLATION", "linear")
    myDynamicCalib.compute_interpolation()
    myDynamicCalib.save()
    print("myDynamicCalib.get_y(2.3)=%f" % myDynamicCalib.get_y(2.3))

    myDynamicCalib.print_info()

    if do_plot:
        myDynamicCalib.plot()

    myDynamicCalib.delete(x=1)
    myDynamicCalib.insert(x=11, y=0)

    if do_plot:
        myDynamicCalib.plot()

def demo_xcalibu_PolyB(do_plot):
    """
    Dynamic Poly calibration
    """

    coeffsB = [0, -0.0004, 0.0223, -0.2574, 1.4143, 1.0227]
    coeffsB = [1, 0, 0]  # cst  x  x2
    coeffsB = [-8, -6, 3, 1]  # cst  x  x2 x3   ===>   -8.0 - 6.0·x¹ + 3.0·x² + 1.0·x³
    # u32a
    coeffsB = [1500.46611131, -1346.88761616, 499.06810627, -97.02312684, 10.45705476, -0.59283464, 0.01382656]

    myCalibPolyB = Xcalibu(calib_name="PolyB", description="Polynom calib deg=? for PolyB")
    myCalibPolyB.set_calib_type("POLY")
    myCalibPolyB.set_coeffs(coeffsB)
    # myCalibPolyB.set_x_limits(-15, 25)  # For POLY, limits are used for plot.
    # myCalibPolyB.set_x_limits(-800, 3800)  # no more increasing after ~33.
    myCalibPolyB.set_x_limits(5, 10)

    myCalibPolyB.set_sampling_nb_points(100)
    myCalibPolyB.check_monotonic()

#    assert numpy.isclose(myCalibPolyB.get_y(0), 1.0227)
#    assert numpy.isclose(myCalibPolyB.get_y(-10), -65.1603)
#    assert numpy.isclose(myCalibPolyB.get_y(22), 51.3037)
    print(f"f(0)={myCalibPolyB.get_y(0)}", end="    ")
    print(f"f(-10)={myCalibPolyB.get_y(-10)}", end="   ")
    print(f"f(22)={myCalibPolyB.get_y(22)}")

    print(f"f(-4)={myCalibPolyB.get_y(-4)}")
    print(f"f(-1)={myCalibPolyB.get_y(-1)}")
    print(f"f(2)={myCalibPolyB.get_y(2)}")

    myCalibPolyB.print_info()

    if do_plot:
        myCalibPolyB.plot()


def demo_xcalibu_poly_cubic(do_plot):
    """
    POLY cubic calibration
    """

    poly_cubic = Xcalibu(calib_file_name=XCALIBU_DIRBASE + "/examples/cubic_poly.calib",
                         reconstruction_method="INTERPOLATION")


    poly_cubic.set_x_limits(1,5)
    poly_cubic.check_monotonic()
    poly_cubic.compute_interpolation()
    poly_cubic.print_info()

    print(f" poly_cubic.get_y( 1 ) = {poly_cubic.get_y(1)}")
    print(f" poly_cubic.get_y( 0 ) = {poly_cubic.get_y(0)}")
    print(f"poly_cubic.get_y( -5 ) = {poly_cubic.get_y(-5)}")
    print(f"poly_cubic.get_y( -9 ) = {poly_cubic.get_y(-9)}")
    print("--------------------------------------------------")
    print(f"poly_cubic.get_x( 12 ) = {poly_cubic.get_x(12)}")


    print("--------------------------------------------------")

    if do_plot:
        poly_cubic.plot()


'''
def demo_xcalibu_(do_plot):
    """
    ... calibration
    """
    log = logging.getLogger("XCALIBU")


    .print_info()

    if do_plot:
        .plot()
'''

'''
def demo_xcalibu_(do_plot):
    """
    ... calibration
    """
    log = logging.getLogger("XCALIBU")

    .print_info()

    if do_plot:
        .plot()
'''

def main():

    """
    arguments parsing
    """
    from optparse import OptionParser

    parser = OptionParser("demo_xcalibu.py")
    parser.add_option(
        "-d",
        "--debug",
        type="string",
        help="Available levels are :\n CRITICAL(50)\n \
                      ERROR(40)\n WARNING(30)\n INFO(20)\n DEBUG(10)",
        default="INFO",
    )

    parser.add_option(
        "-p",
        "--plot",
        action="store_true",
        dest="plot",
        default=False,
        help="Calibration plotting",
    )

    # Gather options and arguments.
    (options, args) = parser.parse_args()
    # print(options)
    # print(args)

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

    LOG_FORMAT = "%(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(format=LOG_FORMAT, level=loglevel)

    print("-------------- args ------------------------")
    print(options)
    print(" plot=", options.plot)
    print("--------------------------------------")

    demo_xcalibu_1(options.plot)
    demo_xcalibu_2(options.plot)
    demo_xcalibu_3(options.plot)
    demo_xcalibu_U32a(options.plot)
    demo_xcalibu_table15(options.plot)
    demo_xcalibu_cubic(options.plot)
    demo_xcalibu_RingRy(options.plot)
    demo_xcalibu_dynamic(options.plot)
    demo_xcalibu_PolyB(options.plot)
    demo_xcalibu_poly_cubic(options.plot)

if __name__ == "__main__":
    main()

"""
 33270 Feb  6 23:31            book5.txt : index + 5 cols
   354 Feb  2 13:56          cubic.calib : 10 points table ~~ cubic func
   416 Feb  2 13:56          gauss.calib : 11 points table, roughly a gaussian...
 12349 Feb  2 13:56    hpz_ring_Ry.calib : 360 points table piezo hexapod metrologic ring calibration
   331 Feb 22 21:00           poly.calib : order 2 poly : 28.78 - 5.57·x¹ + 0.56·x²
    93 Feb  6 23:36   table_1_column.txt : Single column datafile.
   340 Feb  2 13:56    table_2_col.calib : 15 points table calib
   128 Feb 22 21:00  table_2_columns.txt : double columns datafile.
   462 Feb  2 13:56          table.calib : 15 points table calib (legacy format B52[1]=1)
   537 Feb 22 21:00     U32a_1_table.txt : 40 lines 2 cols datafile
   443 Mar 16 13:43      u32a_poly.calib : 6th order poly
   476 Feb 22 21:00     undu_table.calib : 12 lines table
   375 Feb  2 13:56 unsorted_table.calib : 5 lines table
"""
