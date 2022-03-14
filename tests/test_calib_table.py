import pytest
import numpy as np
import time

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
    assert calib.nb_calib_points == 15
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

    # test 2 columns with various float number format
    calib = xcalib_demo("table_2_col.calib")
    assert calib.nb_calib_points == 15
    assert calib.get_y(6) == -3
    assert calib.get_y(6.5) == -0.5

    with pytest.raises(XCalibError):
        calib.get_y(-1)  # out of range


def test_poly(xcalib_demo):
    """
    test poly calib.
    """
    poly_calib = xcalib_demo("poly.calib")  # X in [5;15]

    assert poly_calib.get_y(5) == pytest.approx(14.93)
    assert poly_calib.get_y(15) == pytest.approx(71.23)

    # Reverse calculation
    # assert poly_calib.get_x(71.23) == pytest.approx(15.00)


def test_table_fit(xcalib_demo):
    """
    Test fit of points of a table
    """
    cubi = xcalib_demo("cubic.calib")
    cubi.set_fit_order(3)
    cubi.set_reconstruction_method("POLYFIT")
    cubi.fit()
    # print(f"fit order = {cubi.get_fit_order()} coeffs={cubi.coeffs} ")

    # CALIB_DESC = "roughly  y=0.03x^{3}+0.02x^{2}+0.01x+1"
    np.testing.assert_almost_equal(cubi.coeffs, np.array([0.03, 0.02, 0.01, 1.0]), decimal=2)

    assert cubi.get_y(-2.32) == pytest.approx(0.705162560)


def test_input_array(xcalib_demo):
    """
    test of array usage.
    """
    calib = xcalib_demo("unsorted_table.calib")  # X:[1;10] Y:[1;2]
    input_array = np.array([1.0, 1.5, 3.0, 3.5, 8.777, 10.0])
    y_arr = calib.get_y(input_array)

    assert type(y_arr) == type(input_array)
    np.testing.assert_almost_equal(y_arr, np.array([1.0, 1.5, 1.5, 1.25, 2.0, 2.0]))

    t0 = time.time()
    nb_values = 100000
    big_input_array = np.linspace(1.1, 9.5, nb_values)
    calib.get_y(big_input_array)
    print(f"duration for {nb_values} values: {time.time() - t0}")
    # NB: 0.86 s for 100.000 values on a intel xeon E3-1245 CPU @3.5GHz

    # oups...
    # x_arr = calib.get_x(y_arr)
    # np.testing.assert_almost_equal(x_arr, input_array)


def test_input_invalid_array(xcalib_demo):
    """
    test of array usage.
    """
    calib = xcalib_demo("unsorted_table.calib")  # X:[1;10] Y:[1;2]
    invalid_input_array = np.array([0.123, 5.55])

    with pytest.raises(XCalibError):
        calib.get_y(invalid_input_array)
