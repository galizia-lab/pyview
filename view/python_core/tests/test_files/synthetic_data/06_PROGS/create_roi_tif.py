import pathlib as pl

import numpy as np

from view import VIEW
from view.python_core.get_internal_files import get_internal_test_files_path
from view.python_core.io import write_tif_2Dor3D

yml_file = (
    pl.Path(get_internal_test_files_path())
    / "synthetic_data"
    / "view_synthetic_666.yml"
)
animal = "Synthetic_data_strip"
measu = 5
extra_flags = {
    "Data_Median_Filter": 1,
}

vo = VIEW()
vo.update_flags_from_ymlfile(yml_file)
vo.initialize_animal(animal)
vo.update_flags(extra_flags)
vo.load_measurement_data_from_current_animal(measu)
vo.calculate_signals()

pulse_start_frames = vo.p1.pulsed_stimuli_handler.get_pulse_start_frames()

frames_to_consider = slice(min(pulse_start_frames), vo.p1.sig1.shape[2])
print(f"frames_to_consider: {frames_to_consider}")
signal_frames_at_stimuli = np.abs(vo.p1.sig1[:, :, frames_to_consider])
roi_array = signal_frames_at_stimuli.max(axis=2).astype(np.float32)

output_tif_file = str(
    pl.Path(vo.flags.get_coor_dir_str()) / f"{vo.get_current_animal()}.roi.tif"
)

write_tif_2Dor3D(
    array_xy_or_xyt=roi_array, tif_file=output_tif_file, dtype=np.float32
)
