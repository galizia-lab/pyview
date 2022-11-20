import pandas as pd
from moviepy.editor import ImageSequenceClip
import multiprocessing
import logging
import pathlib as pl
import numpy as np
import tifffile


def get_extension_from_codec(codec):

    codec_map = {"libx264": ".mp4",
                 "ayuv": ".avi"
                 }

    return codec_map[codec]


class MovieWriter(object):

    def __init__(self, flags):

        super().__init__()
        self.speed_factor = flags["mv_SpeedFactor"]
        self.bitrate = flags["mv_bitrate"]
        self.codec = flags["mv_exportFormat"]

    def get_clip(self, data_numpy_list, data_sampling_period):

        data_fps = pd.Timedelta("1s") / data_sampling_period
        video_fps = self.speed_factor * data_fps

        data_numpy_list_for_moviepy = []

        for frame_data_numpy in data_numpy_list:

            # need to swap axes as our axis order is XY and moviepy expects YX
            frame_data_numpy_swapped = frame_data_numpy.swapaxes(0, 1)

            # need to convert it to 8 bit from float
            frame_data_numpy_swapped_uint8 = np.array(frame_data_numpy_swapped * 255, dtype=np.uint8)

            # flip Y since origin in moviepy is top left
            frame_data_for_clip = np.flip(frame_data_numpy_swapped_uint8, axis=0)

            data_numpy_list_for_moviepy.append(frame_data_for_clip)

        clip = ImageSequenceClip(data_numpy_list_for_moviepy, fps=video_fps)

        return clip

    def write(self, data_numpy_list, data_sampling_period, full_filename_without_extension):

        if data_sampling_period == pd.Timedelta(0):

            raise ValueError("Error saving movie! The inter frame period was either not specified or set to 0, "
                             "the frame-per-second value for movie output could therefore not be calculated.\n"
                             "Tip: You can save the movie as a TIFF-Stack by setting the flags 'mv_exportFormat' in "
                             "the tab 'movie' to 'stack_tif' and view the resulting TIFF-Stack in ImageJ")

        clip = self.get_clip(data_numpy_list, data_sampling_period)

        out_name = f"{full_filename_without_extension}{get_extension_from_codec(self.codec)}"

        ffmpeg_params = []
        if self.codec == "libx264":
            ffmpeg_params = ["-crf", '1']

        clip.write_videofile(filename=out_name,
                             codec=self.codec,
                             ffmpeg_params=ffmpeg_params,
                             preset="veryslow",
                             threads=multiprocessing.cpu_count() - 1,
                             logger="bar",
                             bitrate=self.bitrate
                             )
        logging.getLogger("VIEW").info(f"Wrote a movie: {out_name}")
        return out_name


class MovieWriterIndividualTif(MovieWriter):

    def __init__(self, flags):

        super().__init__(flags)

    def write(self, data_numpy_list, data_sampling_period, full_filename_without_extension):

        if data_sampling_period == pd.Timedelta(0):
            data_sampling_period = pd.Timedelta("1s")  # fake value, as it will not be written

        clip = self.get_clip(data_numpy_list, data_sampling_period)

        out_dir_path = pl.Path(full_filename_without_extension)
        if not out_dir_path.is_dir():
            out_dir_path.mkdir()

        filename_format = f"{str(out_dir_path / out_dir_path.name)}%03d.tif"

        clip.write_images_sequence(nameformat=filename_format,
                                   logger="bar")
        logging.getLogger("VIEW").info(f"Wrote a sequence of images to the folder {str(out_dir_path)}")

        return out_dir_path


class MovieWriterStackTif(object):

    def __init__(self):

        super().__init__()

    def write(self, data_numpy_list, data_sampling_period, full_filename_without_extension):

        # each image in data_numpy_list is of the format X,Y,Color.
        # Stacking them to get 4D data in the format Z, X, Y, Color
        data_4D = np.stack(data_numpy_list, axis=0)

        # Flip Y since origin in tif is top left
        data_4D_Y_flipped = np.flip(data_4D, axis=2)

        # convert to uint8
        data_4D_uint8 = np.array(data_4D_Y_flipped * 255, dtype=np.uint8)

        # convert to format Z, Y, X, color
        data_4D_XY_swapped = data_4D_uint8.swapaxes(1, 2)

        # convert to TZCYXS format required by imagej
        data_4D_formatted = data_4D_XY_swapped[np.newaxis, :, np.newaxis, :, :]

        outfile_path = f"{full_filename_without_extension}.tif"

        tifffile.imwrite(outfile_path, data=data_4D_formatted, imagej=True)
        logging.getLogger("VIEW").info(f"Wrote a tiff stack to {str(outfile_path)}")

        return outfile_path


def get_writer(flags):

    if flags["mv_exportFormat"] == "single_tif":

        return MovieWriterIndividualTif(flags)

    elif flags["mv_exportFormat"] == "stack_tif":

        return MovieWriterStackTif()

    else:
        return MovieWriter(flags)