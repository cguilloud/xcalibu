import pytest

from xcalibu import XCalibError


def test_interpolation_get_y(xcalib_demo):
    calib = xcalib_demo("table.calib")
    assert calib.get_calib_name() == "B52"
    assert calib.get_calib_type() == "TABLE"
    assert calib.get_y(6) == -3
    assert calib.get_y(6.5) == -0.5
    
    with pytest.raises(XCalibError):
        calib.get_y(-1)  # out of range


def test_interpolation_unsorted(xcalib_demo):
    calib = xcalib_demo("unsorted_table.calib")
    assert calib.get_y(4) == 1
    assert calib.get_y(4.5) == 1.5
    assert calib.get_y(8) == 2


def test_edit_table(xcalib_demo):
    calib = xcalib_demo("unsorted_table.calib")
    assert calib.get_y(4) == 1
    calib.del_x(4)
    assert calib.get_y(4) == 1
    with pytest.raises(XCalibError):
        calib.del_x(4)  # does not exist in table

    assert calib.get_y(4) == 1
