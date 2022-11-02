import logging


def get_background_frames(p1_metadata, flags):

    onset_frame_first_stimulus = p1_metadata.pulsed_stimuli_handler.get_first_stimulus_onset_frame()
    default_background = flags["LE_DefaultBackgroundRange"]

    if flags["LE_StimulusBasedBackground"] and onset_frame_first_stimulus is not None:

        LE_StartBackground = flags["LE_StartBackground"]
        LE_PrestimEndBackground = flags["LE_PrestimEndBackground"]
        end_background = onset_frame_first_stimulus - LE_PrestimEndBackground
        if end_background <= LE_StartBackground:
            logging.getLogger("VIEW").warning(
                f"Encountered end_background <= start_background, which is invalid. "
                f"Defaulting to the background range {default_background}")
            return default_background
        else:
            return (LE_StartBackground, end_background)

    else:

        logging.getLogger("VIEW").warning(
            f"No stimuli information specified in measurement list file. "
            f"Or LE_StimulusBasedBackground set to false. "
            f"Defaulting to the background range {default_background}")
        return default_background

