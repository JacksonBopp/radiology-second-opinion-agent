import pytest
from pydicom.data import get_testdata_file


@pytest.fixture
def ct_dicom_path() -> str:
    return get_testdata_file("CT_small.dcm")


@pytest.fixture
def mr_dicom_path() -> str:
    return get_testdata_file("MR_small.dcm")
