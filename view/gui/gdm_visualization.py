from PyQt5.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QComboBox, QHBoxLayout, QFormLayout, QPushButton
from PyQt5.QtCore import pyqtSignal, pyqtSlot
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib import pyplot as plt
import numpy as np
from view.python_core.gdm_generation import get_roi_gdm_traces_dict
from view.python_core.overviews import generate_overview_image, prep_overview_for_output, \
    colorize_overview_add_border_etc
from view.python_core.rois.roi_io import get_roi_io_class


class MplCanvas(FigureCanvasQTAgg):

    def __init__(self, parent=None, width=5.0, height=4.0, dpi=100):
        fig = plt.Figure(figsize=(width, height), dpi=dpi, constrained_layout=True)
        self.axes = fig.add_subplot(111)
        super(MplCanvas, self).__init__(fig)


class GDMViz(QMainWindow):

    def __init__(self, p1, flags):

        super().__init__()

        flags_copy = flags.copy()

        flags_copy.update_flags({
            "SO_xgap": 0,
            "CTV_Method": 300, "SO_Method": 0, "SO_individualScale": 3,
            "SO_MV_colortable": "gray",
            "SO_showROIs": f"3{flags['RM_ROITrace']}",
            "SO_withinArea": True,
            "SO_bgColor": "k",
            "SO_thresholdShowImage": "bgColor"
        })

        self.stimuli_frames = p1.pulsed_stimuli_handler.get_pulse_start_end_frames(allow_fractional_frames=True)

        # data is in X, Y, color format
        self.overview_frame_clean, data_limits, overview_generator_used = \
            colorize_overview_add_border_etc(overview_frame=p1.foto1, flags=flags_copy, p1=None)

        roi_mask_color_label_tuples = overview_generator_used.roi_marker.roi_mask_color_label_tuples

        # if the original size along a dimension is odd, it gets padded by one pixel to make it even.
        # E.g.: if the original data is 153x106, overview generated is 154x106
        # so need to resize masks
        self.roi_mask_dict = {}
        for x, y, z in roi_mask_color_label_tuples:
            if x.shape[0] < self.overview_frame_clean.shape[0] or \
                    x.shape[1] < self.overview_frame_clean.shape[1]:

                enlarged_mask = np.zeros(self.overview_frame_clean.shape[:2], dtype=bool)
                enlarged_mask[:x.shape[0], :x.shape[1]] = x
            else:
                enlarged_mask = x

            self.roi_mask_dict[z] = (enlarged_mask, y)

        roi_data_dict = overview_generator_used.roi_marker.roi_data_dict
        self.roi_label_trace_dict = get_roi_gdm_traces_dict(p1=p1, flags=flags, roi_data_dict=roi_data_dict)

        self.overview_canvas = MplCanvas(self, width=5, height=4, dpi=300)
        self.overview_canvas.figure.suptitle(
            "Pixels outside the area mask are black. "
            "Pixels inside indicates \nvalues of the morphological image (foto1). "
            "Each ROI has a different color,\n and selected ROIs a slightly brighter", size=4)

        overview_for_output = prep_overview_for_output(self.overview_frame_clean)
        self.overview_canvas.axes.imshow(np.flip(overview_for_output, axis=0), origin="lower")
        self.overview_canvas.axes.tick_params(labelsize=4)

        # fake points for label
        for label, (_, color) in self.roi_mask_dict.items():
            self.overview_canvas.axes.plot([0], [0], color=color, ls="-", label=label)

        self.overview_canvas.axes.legend(
            bbox_to_anchor=(1.05, 1), loc="upper left",
            ncol=3, markerscale=0.5, title_fontsize=6, fontsize=4, title="ROI label"
        )

        self.overview_canvas.draw_idle()

        centralWidget = QWidget(self)
        main_vbox = QVBoxLayout(centralWidget)

        top_hbox = QHBoxLayout()
        choosers_formlayout = QFormLayout()
        self.roi_choosers = []
        for i in range(3):
            roi_chooser = QComboBox(parent=centralWidget)
            roi_chooser.addItems(list(roi_data_dict.keys()) + ["---Choose a ROI to visualize---"])
            roi_chooser.setCurrentText("---Choose a ROI to visualize---")
            self.roi_choosers.append(roi_chooser)
            choosers_formlayout.addRow(f"ROI {i}", roi_chooser)

        refresh_button = QPushButton("Refresh overview and traces")
        refresh_button.clicked.connect(self.refresh)
        choosers_formlayout.addWidget(refresh_button)

        top_hbox.addLayout(choosers_formlayout)
        top_hbox.addWidget(self.overview_canvas)

        main_vbox.addLayout(top_hbox)

        self.trace_canvas = MplCanvas(self, width=5, height=4, dpi=300)

        main_vbox.addWidget(self.trace_canvas)
        
        self.setCentralWidget(centralWidget)

        # set one the choice of one of the chooser as an example
        self.roi_choosers[0].setCurrentText(roi_mask_color_label_tuples[0][-1])
        self.refresh()

        self.setWindowTitle("GDM Visualizer")

    @pyqtSlot(name="refresh signal")
    def refresh(self):

        self.trace_canvas.axes.cla()

        chosen_labels = [x.currentText() for x in self.roi_choosers
                         if x.currentText() != "---Choose a ROI to visualize---"]
        for chosen_label in chosen_labels:

            chosen_mask, chosen_roi_color = self.roi_mask_dict[chosen_label]

            trace = self.roi_label_trace_dict[chosen_label]
            self.trace_canvas.axes.plot(
                trace,
                ls="-", marker=None, color=chosen_roi_color
            )

        for this_stimulus_frames in self.stimuli_frames:
            self.trace_canvas.axes.axvspan(*this_stimulus_frames, color="gray", alpha=0.5, edgecolor=None)

        self.trace_canvas.axes.set_ylabel("deltaF/F (a.u.)", size=4)
        self.trace_canvas.axes.set_xlabel("Frame number (0, 1, 2...)", size=4)
        self.trace_canvas.axes.grid(True)
        self.trace_canvas.axes.tick_params(labelsize=4, grid_color="k", grid_linestyle="--", grid_alpha=0.1)
        x_end = self.trace_canvas.axes.get_xlim()[1]
        self.trace_canvas.axes.set_xticks(np.linspace(0, x_end, 10).astype(int))
        self.trace_canvas.draw_idle()






