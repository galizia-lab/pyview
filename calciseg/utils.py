'''
Utility functions for calciseg.
'''


import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import pandas as pd


def compute_std_projection(movie):
    """
    Compute the STD projection over time.

    Parameters
    ----------
    movie : ndarray, shape (H, W, T)

    Returns
    -------
    std_img : ndarray, shape (H, W)
    """
    return movie.std(axis=2)


def compute_mean_projection(movie):
    return movie.mean(axis=2)


import tifffile
import csv

def save_tiff_image(input_2D_image, path):
    tifffile.imwrite(path, input_2D_image.astype(np.float32))


def save_roi_list(seeds, path):
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["y", "x"])
        for y, x in seeds:
            w.writerow([y, x])

import matplotlib.pyplot as plt

def label_image_to_color(labels, cmap='tab20'):
    """
    Convert label image into an RGB image using a colormap.
    Background=0 becomes black.
    """
    cmap_obj = plt.get_cmap(cmap)
    max_label = labels.max()

    # Normalize labels to 0..1
    norm = labels.astype(float) / max_label if max_label > 0 else labels

    # Apply colormap (returns RGBA)
    colored = cmap_obj(norm)[..., :3]  # drop alpha channel

    return colored



def rois_to_label_image(rois):
    """
    rois: list of boolean masks of shape (H, W)
    returns: 2D integer label map (H, W)
    """

    if len(rois) == 0:
        raise ValueError("No ROIs provided!")

    height, width = rois[0].shape
    label_image = np.zeros((height, width), dtype=np.int32)

    for idx, mask in enumerate(rois, start=1):   # labels start at 1
        label_image[mask] = idx

    return label_image


def z_scale_movie(movie):
    """
    movie: 3D numpy array (T, X, Y)
    returns every frame z-scaled to 
    """
    T, X, Y = movie.shape
    scaled_movie = np.empty_like(movie, dtype=np.float32)
    for t in range(T):
        frame = movie[t]
        mean = frame.mean()
        std = frame.std()
        if std > 0:
            scaled_movie[t] = (frame - mean) / std
        else:
            scaled_movie[t] = frame - mean  # all pixels same value
    print(f"Z-scaling done on {T} frames.")
    return scaled_movie 
    


def manual_circle_roi_picker(
    image,
    initial_diameter=21.0,
    name_prefix="circle"
):
    """
    Parameters
    ----------
    image : 2D numpy array (H, W)
    initial_diameter : float
        Default diameter for new ROIs
    name_prefix : str
        Prefix for ROI names

    Returns
    -------
    pandas.DataFrame with columns:
        name, x, y, diameter
    """

    fig, ax = plt.subplots()
    ax.imshow(image, cmap="gray")
    ax.set_title(
        "Left-click: add ROI | Right-click: select ROI | Scroll: resize | Enter: finish"
    )

    rois = []
    circles = []
    active_idx = None

    def add_roi(x, y):
        nonlocal active_idx
        radius = initial_diameter / 2
        circ = Circle((x, y), radius, fill=False, color="red", linewidth=2)
        ax.add_patch(circ)

        rois.append({
            "name": f"{name_prefix} {len(rois) + 1}",
            "x": x,
            "y": y,
            "diameter": initial_diameter
        })
        circles.append(circ)
        active_idx = len(rois) - 1
        highlight_active()
        fig.canvas.draw_idle()

    def highlight_active():
        for i, c in enumerate(circles):
            c.set_edgecolor("yellow" if i == active_idx else "red")

    def find_nearest(x, y):
        if not rois:
            return None
        dists = [
            np.hypot(r["x"] - x, r["y"] - y) for r in rois
        ]
        return int(np.argmin(dists))

    def on_click(event):
        nonlocal active_idx
        if event.inaxes != ax:
            return

        if event.button == 1:  # left click
            add_roi(event.xdata, event.ydata)

        elif event.button == 3:  # right click
            idx = find_nearest(event.xdata, event.ydata)
            if idx is not None:
                active_idx = idx
                highlight_active()
                fig.canvas.draw_idle()

    def on_scroll(event):
        if active_idx is None:
            return
        step = 1.0
        if event.button == "up":
            rois[active_idx]["diameter"] += step
        elif event.button == "down":
            rois[active_idx]["diameter"] = max(
                1.0, rois[active_idx]["diameter"] - step
            )

        circles[active_idx].radius = rois[active_idx]["diameter"] / 2
        fig.canvas.draw_idle()

    def on_key(event):
        if event.key == "enter":
            plt.close(fig)

    fig.canvas.mpl_connect("button_press_event", on_click)
    fig.canvas.mpl_connect("scroll_event", on_scroll)
    fig.canvas.mpl_connect("key_press_event", on_key)

    plt.show()

    return pd.DataFrame(rois)



# some code to do debugging. Will not be used when loaded as library
def debug_manual_circle_roi_picker():
    # Example projection image
    image = np.random.rand(256, 256)

    df = manual_circle_roi_picker(image)

    # Save as tab-delimited text
    df.to_csv("rois.txt", sep="\t", index=False)
    print(df)

if __name__ == "__main__":
    debug_manual_circle_roi_picker()
