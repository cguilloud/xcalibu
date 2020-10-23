import os
import pytest

from xcalibu import Xcalibu

XCALIBU = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


@pytest.fixture
def demo_calib_path():
    def _path(calib_file=None):
        return f"{XCALIBU}/xcalibu/examples/{calib_file}"
    
    return _path

    
@pytest.fixture
def xcalib_demo(demo_calib_path):
    def _calib(calib_file="table.calib", rec_method="INTERPOLATION"):
        calib = Xcalibu(calib_file_name=demo_calib_path(calib_file))
        calib.set_reconstruction_method(rec_method)
        return calib

    return _calib
