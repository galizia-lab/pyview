from common import initialize_test_yml_list_measurement
from view import VIEW
from view.python_core.io import read_tif_2Dor3D, write_tif_2Dor3D
import tempfile
import pathlib as pl
import numpy as np


def test_tif_io():
    test_yml, test_animal, test_measu = initialize_test_yml_list_measurement()

    view = VIEW()

    view.update_flags_from_ymlfile(test_yml)

    view.initialize_animal(test_animal)
    view.load_measurement_data_from_current_animal(test_measu)

    temp_tif_fn = str(pl.Path(tempfile.gettempdir()) / f"{tempfile.gettempprefix()}.tif")

    write_tif_2Dor3D(view.p1.raw1, temp_tif_fn)

    read_stack, labels = read_tif_2Dor3D(temp_tif_fn)

    assert np.allclose(view.p1.raw1, read_stack)
    assert labels is None

    # needs to fix reading labels
    # write_tif_2Dor3D(view.p1.raw1[:, :, 0], temp_tif_fn, labels="test")
    #
    # read_stack, labels = read_tif_2Dor3D(temp_tif_fn)
    #
    # assert np.allclose(view.p1.raw1[:, :, 0], read_stack)
    # assert labels == ["test"]
    #
    # fake_labels = [str(x) for x in range(view.p1.raw1.shape[2])]
    # write_tif_2Dor3D(view.p1.raw1, temp_tif_fn, labels=fake_labels)
    #
    # read_stack, read_labels = read_tif_2Dor3D(temp_tif_fn)
    #
    # assert np.allclose(view.p1.raw1, read_stack)
    # assert all(x == y for x, y in zip(fake_labels, read_labels))


if __name__ == '__main__':

    test_tif_io()

