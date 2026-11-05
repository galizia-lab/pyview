import numpy as np
from tkinter import Tk, filedialog
import tifffile


def select_tiff_file(title="Select a TIFF movie"):
    """
    Open a file dialog and let the user select a TIFF file.

    Returns
    -------
    path : str or None
        Selected file path, or None if canceled.
    """

    root = Tk()
    root.withdraw()  # hide main Tk window

    path = filedialog.askopenfilename(
        title=title,
        filetypes=[("TIFF files", "*.tif *.tiff"), ("All files", "*.*")]
    )

    root.update()
    root.destroy()

    return path if path else None


def load_tiff_movie(path):
    """
    Load a 3D TIFF file (H, W, T) into a NumPy float32 array.

    Parameters
    ----------
    path : str
        Path to TIFF movie.

    Returns
    -------
    movie : ndarray, shape (H, W, T), dtype=float32
    info  : dict
        Metadata from tifffile (tags, imagej metadata, etc.)
    """

    with tifffile.TiffFile(path) as tif:
        arr = tif.asarray()
        metadata = {
            "n_pages": len(tif.pages),
            "imagej_metadata": tif.imagej_metadata,
            "tiff_tags": {tag.name: tag.value for tag in tif.pages[0].tags.values()}
        }

    # Ensure array is float32
    arr = arr.astype(np.float32, copy=False)

    # Make sure shape is (H, W, T)
    if arr.ndim == 3:
        if arr.shape[0] < arr.shape[2]:  
            # Sometimes files come as (T, H, W)
            arr = np.transpose(arr, (1, 2, 0))
    else:
        raise ValueError(
            f"Expected a 3D TIFF, got array with shape {arr.shape}."
        )

    return arr, metadata


def load_movie_via_dialog(title="Select a TIFF movie"):
    """
    Full workflow:
    - open dialog
    - load TIFF
    - return movie + metadata

    Returns
    -------
    movie : ndarray or None
    metadata : dict or None
    """

    path = select_tiff_file(title)
    if path is None:
        return None, None

    movie, metadata = load_tiff_movie(path)
    return movie, metadata, path
