from view.python_core.utils.pil_helpers import add_string
from PIL.ImageDraw import Draw
from view.python_core.utils.colors import mpl_color_to_PIL
from view.python_core.utils.fonts import get_maximum_font_size_by_width


class NoStimulus(object):

    def __init__(self, pulsed_stimuli_handler):

        super().__init__()
        self.pulsed_stimuli_handler = pulsed_stimuli_handler
        self.font_size = None

    def get_frame_odor_conc(self, frame_time):

        [odors], [concs] = self.pulsed_stimuli_handler.get_odor_info_at_times([frame_time])

        return odors, concs

    def mark(self, img, frame_time):

        odors, concs = self.get_frame_odor_conc(frame_time)

        if len(odors) > 0 and len(concs) > 0:
            return self.add_mark_to_image(img, odors[0], concs[0])
        else:
            return img

    def add_mark_to_image(self, img, odor, conc):

        return img


class SquareStimulus(NoStimulus):

    def __init__(self, mv_xgap, mv_ygap, fg_color_for_pil, pulsed_stimuli_handler):

        super().__init__(pulsed_stimuli_handler)
        self.square_side = int(0.5 * mv_ygap)
        self.top_left_xy = (mv_xgap, int(0.25 * mv_ygap))
        self.fg_color = fg_color_for_pil

    def add_mark_to_image(self, img, odor, conc):

        img_draw_obj = Draw(img)
        img_draw_obj.rectangle(xy=(*self.top_left_xy,
                                   self.top_left_xy[0] + self.square_side,
                                   self.top_left_xy[1] + self.square_side),
                               fill=self.fg_color,
                               width=0)
        return img


class SquareStimulusRed(SquareStimulus):

    def __init__(self, mv_xgap, mv_ygap, pulsed_stimuli_handler):
        super().__init__(mv_xgap=mv_xgap, mv_ygap=mv_ygap, pulsed_stimuli_handler=pulsed_stimuli_handler,
                         fg_color_for_pil=mpl_color_to_PIL("r"))


class BaseTextStimulus(NoStimulus):

    def __init__(self, mv_xgap, mv_ygap, fg_color_for_pil, pulsed_stimuli_handler, font_file,
                 frame_size):

        super().__init__(pulsed_stimuli_handler)
        self.mv_xgap = mv_xgap
        self.mv_ygap = mv_ygap
        self.fg_color_for_pil = fg_color_for_pil
        self.font_file = font_file

        all_odors = pulsed_stimuli_handler.stimulus_frame["Odor"]
        all_concs = pulsed_stimuli_handler.stimulus_frame["Concentration"]

        stimulus_strings = [self.compose_stim_text(odor, conc) for odor, conc in zip(all_odors, all_concs)]
        stimulus_string_lengths = [len(x) for x in stimulus_strings]
        longest_stimulus_string = stimulus_strings[stimulus_string_lengths.index(max(stimulus_string_lengths))]

        self.font_size = get_maximum_font_size_by_width(
            maximum_width=frame_size[0], text=longest_stimulus_string, font_name=font_file)

    def add_mark_to_image(self, img, odor, conc):

        stim_y_pos = self.mv_ygap * 0.95
        stim_text = self.compose_stim_text(odor, conc)
        img_with_stim = add_string(img, text=stim_text,
                                   position=(self.mv_xgap, stim_y_pos),
                                   font_size=self.font_size, fill_color_for_pil=self.fg_color_for_pil,
                                   horizontal_alignment="left", vertical_alignment="bottom", font_file=self.font_file)

        return img_with_stim


class OdorConcTextStimulus(BaseTextStimulus):

    def __init__(self, mv_xgap, mv_ygap, fg_color_for_pil, pulsed_stimuli_handler, font_file,
                 frame_size):

        super().__init__(
            mv_xgap, mv_ygap, fg_color_for_pil, pulsed_stimuli_handler, font_file,frame_size)

    def compose_stim_text(self, odor, conc):
        return f"{odor}@{conc}"


class OdorTextStimulus(BaseTextStimulus):

    def __init__(self, mv_xgap, mv_ygap, fg_color_for_pil, pulsed_stimuli_handler, font_file,
                 frame_size):

        super().__init__(
            mv_xgap, mv_ygap, fg_color_for_pil, pulsed_stimuli_handler, font_file,frame_size)

    def compose_stim_text(self, odor, conc):
        return f"{odor}"


def get_stimulus_marker(mv_markStimulus, left_xgap, mv_ygap, color_for_pil, pulsed_stimuli_handler,
                        font_file, frame_size):

    if mv_markStimulus == 0:

        return NoStimulus(pulsed_stimuli_handler=pulsed_stimuli_handler)

    elif mv_markStimulus == 1:

        return SquareStimulus(mv_xgap=left_xgap, mv_ygap=mv_ygap, fg_color_for_pil=color_for_pil,
                              pulsed_stimuli_handler=pulsed_stimuli_handler)

    elif mv_markStimulus == 2:

        return OdorConcTextStimulus(
            mv_xgap=left_xgap, mv_ygap=mv_ygap, fg_color_for_pil=color_for_pil,
            pulsed_stimuli_handler=pulsed_stimuli_handler, font_file=font_file,
            frame_size=frame_size)

    elif mv_markStimulus == 21:

        return OdorTextStimulus(
            mv_xgap=left_xgap, mv_ygap=mv_ygap, fg_color_for_pil=color_for_pil,
            pulsed_stimuli_handler=pulsed_stimuli_handler, font_file=font_file,
            frame_size=frame_size)

    elif mv_markStimulus == 3:

        return SquareStimulusRed(mv_xgap=left_xgap, mv_ygap=mv_ygap, pulsed_stimuli_handler=pulsed_stimuli_handler)
    else:

        raise NotImplementedError
