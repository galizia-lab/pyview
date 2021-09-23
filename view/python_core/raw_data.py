from tillvisionio.vws import load_pst


class AbstractRawData(object):

    def __init__(self, metadata_objects):

        self.paths_metadata = metadata_objects["paths"]
        self.microscope_metadata = metadata_objects["microscope"]
        self.stimulus_metadata = metadata_objects["stimulus"]
        self.animal_metadata = metadata_objects["animal"]

        self.raw_data = None
        self.signal_data = None


class AbstractTillRawData(AbstractRawData):

    def __init__(self, metadata_objects):

        super().__init__(metadata_objects)
        self.raw_filename_ext = ".pst"

    def read_data_n_wavelengths(self, n_wavelengths):

        raw_data = []

        for raw_data_filename_stem in self.paths_metadata.get_raw_filenames_stems(n_wavelengths):

            this_raw_data = load_pst(f"{raw_data_filename_stem}{self.raw_filename_ext}")
            raw_data.append(this_raw_data)

        return raw_data


class TillRawSingeWavelength(AbstractTillRawData):

    def __init__(self, metadata_objects):

        super().__init__(metadata_objects)

        self.raw_data = self.read_data_n_wavelengths(1)[0]


class TillRawDataFura(AbstractTillRawData):

    def __init__(self, metadata_objects):

        super().__init__(metadata_objects)

        self.raw_data = self.read_data_n_wavelengths(2)


def get_raw_data(metadata_objects):

    LE_loadExp = metadata_objects["microscope"].LE_loadExp

    if LE_loadExp == 3:

        return TillRawSingeWavelength(metadata_objects)

    elif LE_loadExp == 4:

        return TillRawDataFura(metadata_objects)

    else:
        raise NotImplementedError




