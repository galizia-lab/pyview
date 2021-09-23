from .io import read_tif_2Dor3D
import matplotlib.pyplot as plt
import logging
import numpy as np


def get_foto1_data(flags, p1):

    foto1_filename = flags.get_existing_filename_in_coor(p1.metadata.ex_name, ".morpho.tif")
    if foto1_filename is not None:
        foto1_data, _ = read_tif_2Dor3D(foto1_filename).astype(np.int32)
    else:
        logging.getLogger("VIEW").warning(f"Could not find {foto1_filename}. Using frame averaged data instead")
        foto1_data = p1.foto1

    return foto1_data


def show_photo(foto1_data):

    if not plt.isinteractive():
        plt.ion()

    fig, ax = plt.subplots()
    ax.imshow(foto1_data.swapaxes(0, 1), cmap="gray", origin="lower")
    fig.canvas.draw()

    plt.show(block=False)


def calc_foto1(raw1):

    return raw1[:, :, 1:6].mean(axis=2)
