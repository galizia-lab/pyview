import numpy as np


class LinearNormalizer(object):

    def __init__(self, vmin, vmax):

        super().__init__()
        self.vmin = vmin
        self.vmax = vmax

    def scale_with_revised_limits_to01(self, data_clipped, vmin2use, vmax2use):

        data_scaled = (data_clipped - vmin2use) / (vmax2use - vmin2use)

        return data_scaled

    def normalize(self, data):

        data_clipped = np.clip(data, self.vmin, self.vmax)

        return self.scale_with_revised_limits_to01(data_clipped, self.vmin, self.vmax)

    def get_data_limits(self):
        """
        Return the lower and upper limits of data as a tuple
        :return: tuple
        """

        return self.vmin, self.vmax


class LinearNormalizerAcross0(LinearNormalizer):

    def __init__(self, vmin, vmax):

        assert (vmin < 0) & (vmax > 0), "LinearScaleAcross0 only works when vmin < 0 and vmax > 0"

        super().__init__(vmin, vmax)


class BilinearNormalizerCentering0(LinearNormalizerAcross0):

    def __init__(self, vmin, vmax):

        super().__init__(vmin=vmin, vmax=vmax)

    def scale_with_revised_limits_to01(self, data_clipped, vmin2use, vmax2use):

        data_negative_masked_out = np.ma.MaskedArray(data=data_clipped, mask=data_clipped < 0, fill_value=0)
        data_positive_masked_out = np.ma.MaskedArray(data=data_clipped, mask=data_clipped >= 0, fill_value=0)

        data_negative_masked_out_scaled \
            = 0.5 + 0.5 * super().scale_with_revised_limits_to01(data_negative_masked_out, 0, vmax2use)
        data_positive_masked_out_scaled \
            = 0.5 * super().scale_with_revised_limits_to01(data_positive_masked_out, vmin2use, 0)

        return data_negative_masked_out_scaled.filled() + data_positive_masked_out_scaled.filled()


class LinearNormalizerCentering0Symmetric(LinearNormalizerAcross0):

    def __init__(self, vmin=None, vmax=None):

        super().__init__(vmin=vmin, vmax=vmax)
        max_one_sided = max(np.abs(self.vmin), np.abs(self.vmax))
        self.vmin, self.vmax = -max_one_sided, max_one_sided


def get_normalizer(mv_individualScale, vmin, vmax):
    scale_modifier = int(mv_individualScale / 10)

    if scale_modifier == 0 or not (vmin < 0 < vmax):
        scaler_class = LinearNormalizer
    elif scale_modifier == 1:
        scaler_class = BilinearNormalizerCentering0
    elif scale_modifier == 2:
        scaler_class = LinearNormalizerCentering0Symmetric
    else:
        raise NotImplementedError

    return scaler_class(vmin=vmin, vmax=vmax)







