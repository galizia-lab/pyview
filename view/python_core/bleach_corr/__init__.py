from .pixelwise import bleach_correct_pixelwise
from ...idl_translation_core.bleach_correction import fitlogdecay, get_bleach_weights
import numpy as np
import platform
import multiprocessing as mp
import logging


class NoBleachCompensator(object):

    def __init__(self):

        super().__init__()

    def apply(self, stack_xyt: np.ndarray, area_mask: np.ndarray):
        """
        Apply bleach correction to the movie `stack_xyt`
        :param numpy.ndarray stack_xyt: 3D, format XYT
        :param numpy.ndarray area: 2D, formay XY
        :return: bleach corrected movie
        :rtype: numpy.ndarray, same shape and format as `stack_xyt`
        """

        return stack_xyt, None


class BaseBleachCompensator(NoBleachCompensator):

    def __init__(self, flags, p1_metadata, movie_size):
        """
        :param FlagsManager flags:
        :param pandas.Series p1_metadata: experimental metadata
        :param tuple movie_size: raw data size, format XYT
        :return: an object that can be used to apply bleach compensation
        """

        super().__init__()

        self.weights = get_bleach_weights(
            flags=flags, p1_metadata=p1_metadata, movie_size=movie_size,
            exclude_stimulus=flags["LE_BleachExcludeStimulus"])


class PixelWiseBleachCompensatorParallel(BaseBleachCompensator):

    def __init__(self, flags, p1_metadata, movie_size):
        """
        :param FlagsManager flags:
        :param pandas.Series p1_metadata: experimental metadata
        :return: an object that can be used to apply bleach compensation
        """

        super().__init__(flags, p1_metadata, movie_size)
        self.ncpu = mp.cpu_count()

    def apply(self, stack_xyt: np.ndarray, area_mask: np.ndarray):
        """
        Apply bleach correction to the movie `stack_xyt`
        :param numpy.ndarray stack_xyt: 3D, format XYT
        :param numpy.ndarray area_mask: 2D, formay XY
        :return: bleach corrected movie
        :rtype: numpy.ndarray, same shape and format as `stack_xyt`
        """

        return bleach_correct_pixelwise(
            movie=stack_xyt, weights=self.weights, area=area_mask, ncpu=self.ncpu)


class PixelWiseBleachCompensator1CPU(PixelWiseBleachCompensatorParallel):

    def __init__(self, flags, p1_metadata, movie_size):
        """
        :param FlagsManager flags:
        :param pandas.Series p1_metadata: experimental metadata
        :return: an object that can be used to apply bleach compensation
        """

        super().__init__(flags, p1_metadata, movie_size)
        self.ncpu = 1


class UniformBleachCompensator(BaseBleachCompensator):

    def __init__(self, flags, p1_metadata, movie_size):

        super().__init__(flags, p1_metadata, movie_size)
        self.background_frames = p1_metadata.background_frames
        self.show_results = not flags["VIEW_batchmode"]
        self.measurement_label = p1_metadata['ex_name']

    def apply(self, stack_xyt: np.ndarray, area_mask: np.ndarray):

        # converting data temporarily to txy format as it is easier to divide the movie by
        # a frame in this format
        stack_txy = np.moveaxis(stack_xyt, source=-1, destination=0)

        # take average over background frames for all pixels
        F0_frame = stack_xyt[:, :, self.background_frames[0]: self.background_frames[1] + 1].mean(axis=2)

        # divide each frame by F0_frame (background frame)
        F_by_F0_txy = stack_txy / F0_frame

        # apply area_mask
        F_by_F0_txy_masked = F_by_F0_txy * area_mask.astype(int)

        # average each frame to make a curve
        # (some pixels in F0_frame might have values of 0, so F_by_F0_txy might have nans)
        curve = np.nanmean(F_by_F0_txy_masked, axis=(1, 2))

        # apply bleach correction to curve and return the parameters A, K and C
        fitted_curve, (A, K, C) = fitlogdecay(lineIn=curve, weights=self.weights, showresults=self.show_results, measurement_label=self.measurement_label)

        # converting to xyt as it is easier to subtract a trace from all pixels in this format
        F_by_F0_xyt = np.moveaxis(F_by_F0_txy, source=0, destination=-1)

        # the third component ensures that the average intensity of each pixel is not
        # affected by the bleach correction applied
        corrected_F_by_F0_xyt = F_by_F0_xyt - fitted_curve + fitted_curve.mean()

        # converting to txy as it easier to multiply by a frame in this format
        corrected_F_by_F0_txy = np.moveaxis(corrected_F_by_F0_xyt, source=-1, destination=0)

        corrected_raw_txy = corrected_F_by_F0_txy * F0_frame

        # converting back to our stadard format xyt
        raw_corrected = np.moveaxis(corrected_raw_txy, source=0, destination=-1)

        return raw_corrected, (A, K, C)


def get_bleach_compensator(flags, p1_metadata, movie_size):
    """
    Get an object whose "apply" method can apply bleach compensation to a movie
    :param FlagsManager flags:
    :param pandas.Series p1_metadata: experimental metadata
    :return: an object that can be used to apply bleach compensation
    """

    if flags["LE_BleachCorrMethod"] == "None":

        return NoBleachCompensator()

    if flags["LE_BleachCorrMethod"] == "log_pixelwise_1cpu":

        return PixelWiseBleachCompensator1CPU(flags, p1_metadata, movie_size)

    if flags["LE_BleachCorrMethod"] == "log_pixelwise_parallel":

        return PixelWiseBleachCompensatorParallel(flags, p1_metadata, movie_size)

    elif flags["LE_BleachCorrMethod"] == "log_uniform":

        return UniformBleachCompensator(flags, p1_metadata, movie_size)
    else:
        logging.getLogger("VIEW").warning(
            f"Not a valid bleach value: "
            f"LE_BleachCorrMethod={flags['LE_BleachCorrMethod']}  ")
        raise NotImplementedError























