from numpy.core.records import array
import pytest
import numpy as np

from xcalibu import XCalibError


def test_table_load_file(xcalib_demo):
    calib = xcalib_demo("unsorted_table.calib")
    assert calib.get_calib_name() == "ST"
    assert calib.get_calib_type() == "TABLE"
    assert np.array_equal(calib.x_raw, np.array([1., 2., 4., 5., 10.]))
    assert np.array_equal(calib.y_raw, np.array([1., 2., 1., 2., 2.]))
    assert calib.dataset_size() == 5
    assert calib.nb_calib_points == 5
    assert calib.is_in_valid_x_range(0) is False
    assert calib.is_in_valid_x_range(1) is True
    assert calib.is_in_valid_y_range(2) is True
    assert calib.is_in_valid_y_range(2.01) is False
    assert calib.Xmin == 1.
    assert calib.Xmax == 10.
    assert calib.Ymin == 1.
    assert calib.Ymax == 2.


def test_table_interpolation_get_y(xcalib_demo):
    calib = xcalib_demo("table.calib")
    assert calib.get_y(6) == -3
    assert calib.get_y(6.5) == -0.5
    
    with pytest.raises(XCalibError):
        calib.get_y(-1)  # out of range


def test_table_unsorted(xcalib_demo):
    calib = xcalib_demo("unsorted_table.calib")
    assert calib.get_y(4) == 1
    assert calib.get_y(4.5) == 1.5
    assert calib.get_y(8) == 2


def test_table_delete(xcalib_demo):
    calib = xcalib_demo("unsorted_table.calib")
    assert calib.get_y(4) == 1
    calib.delete(x=4)
    assert calib.get_y(4) == 2
    
    with pytest.raises(XCalibError):
        calib.delete(x=4)   # does not exist in table

    with pytest.raises(XCalibError):
        calib.delete(y=2)   # ambiguous

    calib.delete(x=2, y=2)  # not ambiguous


def test_table_insert(xcalib_demo):
    calib = xcalib_demo("unsorted_table.calib")
    assert calib.get_y(4.5) == 1.5
    calib.insert(4.5, 3)
    assert calib.get_y(4.5) == 3
    assert calib.get_y(4.25) == 2

    nb = calib.nb_calib_points
    calib.insert([0, 1], [4, 1])
    assert calib.Xmin == 0
    assert calib.Ymax == 4
    assert calib.nb_calib_points == nb + 2


def test_table_2_columns(xcalib_demo):
    calib = xcalib_demo("table_2_columns.calib")
    assert calib.get_y(5) == 0.475166
    assert calib.get_y(5.25) == 0.495043
