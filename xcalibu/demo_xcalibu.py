#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Examples of calibrations for test and demo purposes.
"""

import logging
import os

from xcalibu import Xcalibu


XCALIBU_DIRBASE = os.path.dirname(os.path.realpath(__file__))


log = logging.getLogger("DEMO_XCALIBU")


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

    if do_plot:
        myCalibString.plot()


def demo_xcalibu_2(do_plot):
    """
    ... calibration
    """
    log = logging.getLogger("XCALIBU")

    log.info("============= POLY calibration from file ========================\n")
    myCalibPoly = Xcalibu(calib_file_name=XCALIBU_DIRBASE + "/examples/poly.calib")
    log.info("xcalibu - TEST - Gap for %f keV : %f" % (5, myCalibPoly.get_y(5)))

    if do_plot:
        myCalibPoly.plot()


def demo_xcalibu_3(do_plot):
    """
    TABLE calibration from file with POLYFIT reconstruction method
    """
    log = logging.getLogger("XCALIBU")

    log.info(
        "====== U32BC1G: undu gap TABLE calibration from file with POLYFIT reconstruction method ====\n"
    )
    myCalib2 = Xcalibu(
        calib_file_name=XCALIBU_DIRBASE + "/examples/undu_table.calib",
        fit_order=2,
        reconstruction_method="POLYFIT",
    )
    log.info("TEST - Gap for %f keV : %f" % (5, myCalib2.get_y(5)))

    print("---------------------------------------------------------------------------")
    print("---------------------------------------------------------------------------")

    if do_plot:
        myCalib2.plot()


'''
def demo_xcalibu_(do_plot):
    """
    ... calibration
    """
    log = logging.getLogger("XCALIBU")


    if do_plot:
        .plot()
'''

'''
def demo_xcalibu_(do_plot):
    """
    ... calibration
    """
    log = logging.getLogger("XCALIBU")


    if do_plot:
        .plot()
'''


def demo_xcalibu(do_plot):
    """
    Create various demo calibrations.
    """

    log.info(
        "===== myCalib3: undu TABLE calibration from file with INTERPOLATION rec. method ======\n"
    )
    myCalib3 = Xcalibu(
        calib_file_name=XCALIBU_DIRBASE + "/examples/table.calib",
        fit_order=2,
        reconstruction_method="INTERPOLATION",
    )
    log.info("TEST - Gap for %f keV : %f" % (1, myCalib3.get_y(1)))
    log.info("TEST - Gap for %f keV : %f" % (2, myCalib3.get_y(2)))
    log.info("TEST - Gap for %f keV : %f" % (4, myCalib3.get_y(4)))
    log.info("TEST - Gap for %f keV : %f" % (9, myCalib3.get_y(9)))
    # errors :
    #    log.info("TEST - Gap for %f keV : %f" % (0.5, myCalib3.get_y(0.5)))
    #    log.info("TEST - Gap for %f keV : %f" % (12, myCalib3.get_y(12)))
    #  myCalib3.get_x(42)

    print("---------------------------------------------------------------------------")
    print("---------------------------------------------------------------------------")

    myCalibCubic = Xcalibu(
        calib_file_name=XCALIBU_DIRBASE + "/examples/cubic.calib",
        fit_order=3,
        reconstruction_method="POLYFIT",
    )

    print("---------------------------------------------------------------------------")
    print("---------------------------------------------------------------------------")

    myCalibRingTz = Xcalibu(
        calib_file_name=XCALIBU_DIRBASE + "/examples/hpz_ring_Tz.calib",
        fit_order=20,
        reconstruction_method="POLYFIT",
    )

    print("---------------------------------------------------------------------------")
    print("---------------------------------------------------------------------------")

    myCalibRingRx = Xcalibu(
        calib_file_name=XCALIBU_DIRBASE + "/examples/hpz_ring_Rx.calib",
        fit_order=5,
        reconstruction_method="POLYFIT",
    )

    print("---------------------------------------------------------------------------")
    print("---------------------------------------------------------------------------")

    myCalibRingRy = Xcalibu(
        calib_file_name=XCALIBU_DIRBASE + "/examples/hpz_ring_Ry.calib",
        fit_order=5,
        reconstruction_method="POLYFIT",
    )
    print("saving table demo....")
    myCalibRingRy.set_calib_file_name("ttt.calib")
    myCalibRingRy.save()

    print("---------------------------------------------------------------------------")
    print("---------------------------------------------------------------------------")

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

    print("---------------------------------------------------------------------------")
    print("------------------------------- PolyB -------------------------------------")

    coeffsB = [0, -0.0004, 0.0223, -0.2574, 1.4143, 1.0227]
    coeffsB = [1, 0, 0]  # cst  x  x2

    coeffsB = [-8, -6, 3, 1]  # cst  x  x2 x3   ===>   -8.0 - 6.0·x¹ + 3.0·x² + 1.0·x³

    # u32a
    coeffsB = [1500.46611131, -1346.88761616, 499.06810627, -97.02312684, 10.45705476, -0.59283464, 0.01382656]

    myCalibPolyB = Xcalibu(calib_name="PolyB", description="Polynom calib deg=? for PolyB")
    myCalibPolyB.set_calib_type("POLY")
    myCalibPolyB.set_coeffs(coeffsB)
    # myCalibPolyB.set_x_limits(-15, 25)  # For POLY, limits are used for plot.
    myCalibPolyB.set_x_limits(-8, 38)  # no more increasing after ~33.
    myCalibPolyB.set_x_limits(5, 10)
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

    print("---------------------------------------------------------------------------")
    print("---------------------------------------------------------------------------")

    """
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
    myCalibU32a = Xcalibu(calib_name="U32ATABLE", calib_type="TABLE",
                          calib_file_name=XCALIBU_DIRBASE + "/examples/U32a_1_table.dat",
                          description="2cols table calib of U32A undulator")
    # myCalibU32a.set_reconstruction_method("INTERPOLATION", kind="cubic")
    myCalibU32a.set_reconstruction_method("INTERPOLATION", kind="quadratic")
    myCalibPolyB.check_monotonic()
    myCalibU32a.compute_interpolation()

#    print("get_x(get_y(7))=", myCalibU32a.get_x(float(myCalibU32a.get_y(7))))
    # quadratic -> 7.0000295
    #     cubic -> 6.9997924

#    print("get_x(get_y(7.04))=", myCalibU32a.get_x(float(myCalibU32a.get_y(7.04))))
    # quadratic -> 7.04
    #     cubic -> 7.039999

    if do_plot:
        # myCalibString.plot()    # demo string calibration
        # myCalibPoly.plot()      # order 2 poly
        # myCalib2.plot()         # U32BC1G fit_order=2  ~5..10 -> 15..33
        # myCalib3.plot()         # B52 (crazy lines)     ~0..50->-10..70
        # myDynamicCalib.plot()   # DynCalTable  1..10-> 2..7
        # myCalibCubic.plot()     # CUBIC1
        # myCalibRingTz.plot()    # HPZ_RING_TZ (oscillations) fit_order=20
        # myCalibRingRx.plot()    # HPZ_RING_RX  (sin)
        # myCalibRingRy.plot()    # HPZ_RING_RY
        myCalibPolyB.plot()     # PolyB
        # myCalibPolyD.plot()     # PolyD
        myCalibU32a.plot()      # 59 points TWO_COLS table


# Some data for demo
coeffs_U35A = [0.005827806, -0.2468173, 4.322111, -40.01252, 206.4701, -561.212, 638.7663]

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


if __name__ == "__main__":
    main()
