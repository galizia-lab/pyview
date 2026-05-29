import pytest

from view.gui.tests.conftest import (
    ListLoadTestData,
    default_list_load_test_data,
)  # propagated to tests in this folder # noqa: F401


@pytest.fixture
def default_list_load_test_data_with_roi_file(
    default_list_load_test_data,
) -> ListLoadTestData:

    default_list_load_test_data.roi_path = (
        default_list_load_test_data.test_yml_path.parent
        / "03_COOR"
        / "Synthetic_data_strip.roi"
    )

    default_list_load_test_data.measurement_rows_to_select = (5,)

    return default_list_load_test_data


@pytest.fixture
def default_list_load_test_data_with_coor_file(
    default_list_load_test_data,
) -> ListLoadTestData:

    default_list_load_test_data.roi_path = (
        default_list_load_test_data.test_yml_path.parent
        / "03_COOR"
        / "Synthetic_data_strip.coor"
    )

    default_list_load_test_data.measurement_rows_to_select = (5,)

    return default_list_load_test_data


@pytest.fixture
def default_list_load_test_data_with_roi_tif_file(
    default_list_load_test_data,
) -> ListLoadTestData:

    default_list_load_test_data.roi_path = (
        default_list_load_test_data.test_yml_path.parent
        / "03_COOR"
        / "Synthetic_data_strip.roi.tif"
    )

    default_list_load_test_data.measurement_rows_to_select = (5,)

    return default_list_load_test_data


@pytest.fixture
def default_list_load_test_data_with_area_roi_file(
    default_list_load_test_data,
) -> ListLoadTestData:

    default_list_load_test_data.area_path = (
        default_list_load_test_data.test_yml_path.parent
        / "03_AREAS"
        / "Synthetic_data_strip.area.tif.roi"
    )

    default_list_load_test_data.measurement_rows_to_select = (5,)

    return default_list_load_test_data
