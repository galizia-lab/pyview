import pandas as pd
from bokeh.plotting import figure
from bokeh.palettes import d3
from bokeh.models import Plot, Line, Legend, ColumnDataSource
import numpy as np


def get_bounds(arr):

    arr_min, arr_max = np.nanmin(arr), np.nanmax(arr)

    margin = 0.1 * (arr_max - arr_min)

    return arr_min - margin, arr_max + margin


def add_lineplot(
        data: pd.DataFrame, x: str, y: str, hue: str, bokeh_plot: Plot,
        legend_location: str = "center right", legend_nrow: int = 1,
        legend_click_policy: str = "hide", legend_orientation: str = "vertical",
        white_filled_circle_marker=False, circle_marker_size=8
        ):

    group = data.groupby(hue)

    if len(group) < 3:
        palette = d3["Category10"][3][:len(group)]
    elif 3 <= len(group) <= 10:
        palette = d3["Category10"][len(group)]
    else:
        palette = d3["Category20"][len(group)]

    lines = {}

    for color, (hue, hue_df) in zip(palette, group):

        line = bokeh_plot.line(x=hue_df[x], y=hue_df[y], line_color=color, legend_label=hue)
        lines[hue] = line
        if white_filled_circle_marker:
            bokeh_plot.circle(x=hue_df[x], y=hue_df[y], fill_color="white", size=circle_marker_size)

    bokeh_plot.xaxis.axis_label = x
    bokeh_plot.yaxis.axis_label = y

    bokeh_plot.xaxis.bounds = get_bounds(data[x])
    bokeh_plot.yaxis.bounds = get_bounds(data[y])

    bokeh_plot.legend.click_policy = legend_click_policy
    bokeh_plot.legend.location = legend_location
    bokeh_plot.legend.orientation = legend_orientation

    return bokeh_plot

