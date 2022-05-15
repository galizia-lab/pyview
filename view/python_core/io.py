import tifffile
import numpy as np
import yaml
import pathlib as pl
import datetime as dt
import xml.etree.ElementTree as ET
import logging
import os
from readlif.reader import LifFile


def read_lif(lif_file, measu, load_data=True):
    """
<<<<<<< HEAD
    Read a measurement from a lif file into numpy array. 
    :param str lif_file: path of lif file
    :param int measu: which measurement in the lif file to load
    :param bool load_data: if False, data is not loaded
    :return: numpy.ndarray in XY or XYT format

    Read metadata and return as dictionary
    
    .lif file is Leica lif file
    implemente May 2022, tested with data from Marco Paoli, Toulouse
    
    return: numpy array XYT, metadata dictionary
    
    """
    # if tif_file is str, convert it to path
    # if type(lif_file) == str:
    #     lif_file = pl.Path(lif_file)

    # define metadata -  get default values  
    from view.python_core.p1_class.metadata_related import MetadataDefinition
    meta_def = MetadataDefinition()
    p1_metadata = meta_def.get_default_row()
    # load this dataset
    animal = LifFile(lif_file)
    this_measurement = animal.get_image(measu)
    # extract metadata
    #TODO maybe?
    # better extract matadata by using: convert_lsm_metadata_to_lst_row
    # from /pyview/view/python_core/measurement_list/importers.py
    p1_metadata['Cycle'] = this_measurement.info["settings"]["FrameTime"] #seconds per frame?
    p1_metadata['PxSzX'] = this_measurement.info["scale"][0] #x-size
    p1_metadata['PxSzY'] = this_measurement.info["scale"][1] #y-size
    p1_metadata['SampFreq'] = this_measurement.info["scale"][3] #frames per second?
    p1_metadata['FrameSizeX'] = this_measurement.dims.x #pixel number in x
    p1_metadata['FrameSizeY'] = this_measurement.dims.y #pixel number in x
    p1_metadata['NumFrames'] = this_measurement.dims.t #pixel number in x
    p1_metadata['Measu'] = measu
    p1_metadata['dbb1'] = this_measurement.path
    p1_metadata['Label'] = this_measurement.name
    p1_metadata['Comment'] = "Leica .lif file"
    '''
    I cannot fine the UTC time information yet
                p1_metadata['UTC'] = 
                p1_metadata['MTime'] = 
    animal.xml_header contains a time stamp high and low, maybe that can be used:
    
    animal.xml_header
    Out[107]: '<LMSDataContainerHeader Version="2">
    <Element Name="glom17_210923_bee11.lif" Visibility="1" CopyOption="1" UniqueID="18ec6190-1c45-11ec-ac11-0050622017eb">
    <Data><Experiment Path="E:\\users\\marco\\glom17_210923_bee11.lif" IsSavedFlag="1">
    <TimeStamp HighInteger="30912593" LowInteger="3678550032"/>
    </Experiment></Data>\r\n\t\t<Attributes><Attribute>___Saving</Attribute>
    </Attributes><Memory Size="0" MemoryBlockID="MemBlock_433"/>
    <Children><Element Name="Sequence 001" Visibility="1" CopyOption="1" UniqueID="6e50af8f-1c46-11ec-ac11-0050622017eb">
    <Data><Collection ChildTypeTest="AcceptAll"><ChildTypeList/>
    <TimeStamp HighInteger="30912595" LowInteger="839636880"/>
    <Attachment Name="ACQUISITION_EVENT" Application="LAS AF" Version="1.0">
    <Event Name="Job 1_012" TimeStampHigh="30912595" TimeStampLow="839586880" Type="5" Description="" RelativeTime="0.5284902" ShowInGraph="True" ShowInEventList="True" TrigChannel="-1" TriggerID="0"/><Event Name="Job 1_012" TimeStampHigh="30912595" TimeStampLow="839946880" Type="9" Description="" RelativeTime="0.031" ShowInGraph="True" ShowInEventList="True" TrigChannel="2" TriggerID="0"/></Attachment></Collection></Data>\r\n\t\t\t\t<Memory Size="0" MemoryBlockID="MemBlock_541"/><Children><Element Name="Job 1_012" Visibility="1" CopyOption="1" UniqueID="6e50af92-1c46-11ec-ac11-0050622017eb"><Data><Image TextDescription="            
    
    '''    
        #load data
    if load_data:
        # load this dataset
        #animal = LifFile(lif_file)
        #this_measurement = animal.get_image(measu)
        
        dims = this_measurement.dims
        #dimensions are x, y, z, t, m. We are interested in x, y, t
        img_data = np.zeros((dims.x, dims.y, dims.t), dtype=np.float)

        frame_list   = [i for i in this_measurement.get_iter_t(c=0, z=0)]
        for count, frame in enumerate(frame_list):
            img_data[:,:,count] = np.asarray(frame)

    return img_data, p1_metadata

# end read_lif



def read_tif_2Dor3D(tif_file, flip_y=True, return_3D=False, load_data=True):
    """
    Read a TIF file into numpy array. TIF file axes are assumed to be TYX or YX. Also works for OME Tiff files,
    e.g. Live Acquisition, or FIJI
    :param str tif_file: path of tif file
    :param bool flip_y: whether to flip Y axis
    :param bool return_3D: whether to convert 2D to 3D if required
    :param bool load_data: if True loads data and returns else first return value is None
    :return: data, metadata
    data: numpy.ndarray in XY or XYT format
    metadata: dictionary if present, else None
    
    """
    # if tif_file is str, convert it to path
=======
    Read a TIF file into numpy array. TIF file axes are assumed to be TYX or YX. Also works for OME Tiff files,
    e.g. Live Acquisition, or FIJI
    :param str tif_file: path of tif file
    :param bool flip_y: whether to flip Y axis
    :param bool return_3D: whether to convert 2D to 3D if required
    :param bool load_data: if True loads data and returns else first return value is None
    :return: data, metadata
    data: numpy.ndarray in XY or XYT format
    metadata: dictionary if present, else None
    
    """
    # if tif_file is str, convert it to path
>>>>>>> a476b63c975103c2cd6357311bbcd521129766f9
    if type(tif_file) == str:
        tif_file = pl.Path(tif_file)

    # load metadata
    # tif_file=animal_list[10]
    with tifffile.TiffFile(tif_file) as tif:
            metadata = tif.imagej_metadata
            # imagej_metadata does not work any more or never worked on stack - read metadata from first frame
            if metadata is None:
                metadata = tif.pages[0].description

    # extract XML tree from metadata into root
    try:
        root = ET.fromstring(metadata)
        metadata_present = True

        # define namespace for OME data
        # this uses xTree OME syntax
        # https://docs.python.org/3/library/xml.etree.elementtree.html#xml.etree.ElementTree.Element
        ns = {
            "d": "http://www.openmicroscopy.org/Schemas/OME/2013-06"    
        }
        # now get all infos that we put into settings file
        meta_info = root.find("./d:Image/d:Pixels", ns).attrib
        # result is a dictionary, for example:
     #        {'ID': 'Pixels:1-0',
     # 'DimensionOrder': 'XYTZC',
     # 'Type': 'uint16',
     # 'SizeX': '1392',
     # 'SizeY': '1040',
     # 'SizeZ': '1',
     # 'SizeC': '1',
     # 'SizeT': '160',
     # 'PhysicalSizeX': '6.45',
     # 'PhysicalSizeY': '6.45',
     # 'PhysicalSizeZ': '1000',
     # 'SignificantBits': '14'}
        # acquisition date as string, e.g. '2021-09-19T16:49:28'
        AcquisitionDate = root.find("./d:Image/d:AcquisitionDate", ns).text
        meta_info.update({'AcquisitionDate':AcquisitionDate})
        # binning info, e.g. '1x1'
        Binning = root.find("./d:Image/d:Pixels/d:Channel/d:DetectorSettings", ns).attrib["Binning"]
        meta_info.update({'Binning':Binning})
     # frame interval
        # relative time of secoond image (first image looks unsafe - often it is blanck. Therefore use frames 2 and 3)
        time_frame1 = root.find("./d:Image/d:Pixels/d:Plane[2]", ns).attrib["DeltaT"]
        # relative time of third image
        time_frame2 = root.find("./d:Image/d:Pixels/d:Plane[3]", ns).attrib["DeltaT"]
        GDMfreq = (float(time_frame2) - float(time_frame1))
        GDMfreq = int(GDMfreq*1000 + 0.5) # unit is ms, rounded
        meta_info.update({'GDMfreq':str(GDMfreq)})
    # exposure time for frame 2 - expecting that to be uniform
        ExposureTime_ms = float(root.find("./d:Image/d:Pixels/d:Plane[2]", ns).attrib["ExposureTime"])
        ExposureTime_ms = int(1000*ExposureTime_ms) # value in Andor is in seconds
        meta_info.update({'ExposureTime_ms':str(ExposureTime_ms)})
    # columns in .settings that need to be filled here:
    # get the tif file, including the last directory
        this_filename = tif_file.parts
        dbb = this_filename[-2] +'/'+ this_filename[-1]
        meta_info.update({'dbb':dbb})
        meta_info.update({'Label':this_filename[-1]})
        # PxSzX
        # replace the Andor name "PhysicalSizeX' with the Galizia name PsSzX
        meta_info['PsSzX'] = meta_info.pop('PhysicalSizeX')
        meta_info['PsSzY'] = meta_info.pop('PhysicalSizeY')
        # PxSzY, e.g. 1.5625
    # When was this measurement taken?
    # first get the time when the measurement was started
        measurementtime = dt.datetime.fromisoformat(AcquisitionDate)
    # now add the time of the first frame, since measurement start time ie equal for all measurements in one loop
        measurementtime_delta = dt.timedelta(seconds=float(time_frame1))
        measurementtime = measurementtime + measurementtime_delta
        # StartTime, e.g. 10:05:04
        StartTime = measurementtime.strftime('%H:%M:%S')
        meta_info.update({'StartTime':StartTime})
        # UTC, e.g. 1623229504.482
        UTC = measurementtime.timestamp()
        meta_info.update({'UTCTime':UTC})
    except:
        metadata_present = False
        meta_info = None

    # load data
    if load_data:
        with tifffile.TiffFile(tif_file) as tif:
                imagej_hyperstack = tif.asarray()

        if len(imagej_hyperstack.shape) == 3:  # 3D data in TYX format

            if flip_y:
                imagej_hyperstack = np.flip(imagej_hyperstack, axis=1)

            imagej_hyperstack = imagej_hyperstack.swapaxes(0, 2)  # return in XYT format

        # read 2D tif data
        elif len(imagej_hyperstack.shape) == 2:  # 2D data in YX format

            if flip_y:
                imagej_hyperstack = np.flip(imagej_hyperstack, axis=0)

            imagej_hyperstack = imagej_hyperstack.swapaxes(0, 1)  # YX to XY format
            if return_3D:
                imagej_hyperstack = np.stack([imagej_hyperstack], axis=2)
    else:  # i.e., if load_data is false
        imagej_hyperstack = None

    return imagej_hyperstack, meta_info
# end read_ometif_metadict


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
