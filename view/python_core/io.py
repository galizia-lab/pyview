import tifffile
import numpy as np
import yaml
import pathlib as pl


def read_tif_2Dor3D(tif_file, flip_y=True, return_3D=False):
    """
    Read a TIF file into numpy array. TIF file axes are assumed to be TYX or YX
    :param str tif_file: path of tif file
    :param bool flip_y: whether to flip Y axis
    :param bool return_3D: whether to convert 2D to 3D if required
    :return: numpy.ndarray in XY or XYT format
    """

    with tifffile.TiffFile(tif_file) as tif:

        metadata = tif.pages[0].description
        labels = None

        if type(metadata) is str:
            if metadata.startswith("Labels="):
                labels = metadata[7:].split(";;")

    data_in = tifffile.imread(tif_file)

    if len(data_in.shape) == 3:  # 3D data in TYX format

        if flip_y:
            data_in = np.flip(data_in, axis=1)

        return data_in.swapaxes(0, 2), labels  # return in XYT format

    elif len(data_in.shape) == 2:  # 2D data in YX format

        if flip_y:
            data_in = np.flip(data_in, axis=0)  # YX to XY format

        data_out = data_in.swapaxes(0, 1)
        if return_3D:
            data_out = np.stack([data_out], axis=2)

        return data_out, labels


def read_single_file_fura_tif(tif_file):
    """
    Read FURA data from <tif_file>. Assume input file has the format TWYX, where W is wavelength and
    this dimension has size 2.
    :param str tif_file: absolute path of the file on file system
    :rtype: data_340, data_380
    data_340: 340nm data as an numpy.ndarray, format XYT
    data_380: 380nm data as an numpy.ndarray, format XYT
    """

    data_in = tifffile.imread(tif_file)

    data_in = np.flip(data_in, axis=1)  # format TWYX

    # split data, each will have format TYX
    data_340 = data_in[:, 1, :, :]
    data_380 = data_in[:, 0, :, :]

    return data_340.swapaxes(0, 2), data_380.swapaxes(0, 2)  # return in format XYT


def write_tif_2Dor3D(array_xy_or_xyt, tif_file, dtype=None, scale_data=False, labels=None):
    """
    Write a 2D or a 3D numpy array to a TIFF file with data type format <dtype>. If <dtype> is None, data is written
    in its own data type. Else, the function will try to safely cast data in <array_xy_or_xyt> to <dtype>.
    If it is not possible and <scale_data> is True, data is scaled to fit the dynamic range of <dtype> and
    written to disc. Else an error is raised
    :param numpy.ndarray array_xy_or_xyt: array to be written
    :param str tif_file: name of file to which data is to be written
    :param dtype: data type format to use. Must be a valid numerical numpy dtype
    (https://numpy.org/doc/stable/reference/arrays.scalars.html)
    :param str|Sequence labels: a str or 1 member sequence when <array_xy_or_xyt> is 2D, else a sequence
    with the same size as the last (3rd) dimension of <array_xy_or_xyt>
    """

    if dtype is None:
        array_cast = array_xy_or_xyt
    else:
        if issubclass(dtype, np.integer):
            info = np.iinfo(dtype)
        elif issubclass(dtype, np.flexible):
            info = np.finfo(dtype)
        else:
            raise ValueError(
                "Invalid dtype. Please specify a valid numerical numpy dtype "
                "(https://numpy.org/doc/stable/reference/arrays.scalars.html)")

        if np.can_cast(array_xy_or_xyt, dtype):

            array_cast = array_xy_or_xyt.astype(dtype)

        elif scale_data:

            array_min, array_max = array_xy_or_xyt.min(), array_xy_or_xyt.max()
            array_xy_or_xyt_0_1 = (array_xy_or_xyt - array_min) / (array_max - array_min)

            array_scaled = info.min + array_xy_or_xyt_0_1 * (info.max - info.min)
            array_cast = array_scaled.astype(dtype)

        else:
            raise ValueError(
                f"The values in the specified array could not be safely cast into the specified dtype ({dtype})."
                f"If you want the values in the specified array to be scaled into the dynamic range of {dtype}, "
                f"set the argument <scale_data> to True")

    # flip Y axis
    array_cast = np.flip(array_cast, axis=1)

    if type(labels) is str:
        labels = [labels]

    if len(array_cast.shape) == 2:
        array_to_write = array_cast.swapaxes(0, 1)  # from XY to YX
        if labels is not None:
            assert len(labels) == 1, \
                f"Expected one label to write along with a one page TIF. Got ({len(labels)})"
    elif len(array_cast.shape) == 3:
        array_to_write = array_cast.swapaxes(0, 2)  # from XYT to TYX
        if labels is not None:
            assert len(labels) == array_cast.shape[2], \
                f"Expected {array_cast.shape[2]} labels two write along with array with shape {array_cast.shape}. " \
                f"Got {len(labels)}"
    else:
        raise ValueError("This function can only write 2D or 3D arrays")

    kwargs = {"description": None}
    if labels is not None:
        kwargs["description"] = "Labels=" + ";;".join(labels)

    tifffile.imwrite(file=tif_file, data=array_to_write, **kwargs)


def read_check_yml_file(yml_filename, expected_type=None):
    """
    Reads flags from <filename>, applies some checks and returns them
    :param yml_filename: str, path of a .yml file
    :param expected_type: any, if specified, as assertion error is raised if contents
    of the yml file is not of the specfied type
    :return: any, depending of contents of the yml file
    """

    with open(yml_filename, 'r') as fle:
        yml_contents = yaml.load(fle, yaml.SafeLoader)

    if expected_type is not None:
        assert type(yml_contents) is expected_type, f"YML file {yml_filename} was expected to contain " \
                                                    f"{expected_type} data," \
                                                    f"found, {type(yml_contents)} instead"
    return yml_contents


def write_yml(yml_filename, to_write):

    with open(yml_filename, 'w') as fle:
        yaml.dump(to_write, fle, Dumper=yaml.SafeDumper)

def read_lsm(path):
    """ takes a path to a lsm file, reads the file with the tifffile lib and
   returns a np array
   """
    data_cut = tifffile.imread(path)
    data_cut_rot = np.swapaxes(data_cut, 0, 2)
    data_cut_rot_flip = np.flip(data_cut_rot, axis=1)

    return data_cut_rot_flip


def load_pst(filename):
    """
    read tillvision based .pst files as uint16.
    """
    # filename can have an extension (e.g. .pst), or not
    # reading stack size from inf
    # inf_path = os.path.splitext(filename)[0] + '.inf'
    # this does not work for /data/030725bR.pst\\dbb10F, remove extension by hand,
    # assuming it is exactly 3 elements

    if filename.endswith(".pst") or filename.endswith(".ps"):
        filepath = pl.Path(filename)
    else:
        filepath = pl.Path(f"{filename}.pst")
        if not filepath.is_file():
            filepath = filepath.with_suffix(".ps")

    assert filepath.is_file(), \
        f"Could not find either of the following raw data files:\n{filename}.pst\n{filename}.ps"

    meta = {}
    with open(filepath.with_suffix(".inf"), 'r') as fh:
        #    fh.next()
        for line in fh.readlines():
            try:
                k, v = line.strip().split('=')
                meta[k] = v
            except:
                pass
    # reading stack from pst
    shape = np.int32((meta['Width'], meta['Height'], meta['Frames']))

    expected_units = np.prod(shape)

    assert filepath.stat().st_size >= 2 * expected_units, \
        f"Expected at least {2 * expected_units} bytes in {filepath}. Found {filepath.stat().st_size}"

    raw = np.fromfile(filepath, dtype='int16', count=expected_units)
    data = np.reshape(raw, shape, order='F')

    # was swapping x, y axes; commented out to retain original order
    # data  = data.swapaxes(0,1)

    # data is upside down as compared to what we see in TillVision
    data = np.flip(data, axis=1)
    data = data.astype('uint16')
    return data
