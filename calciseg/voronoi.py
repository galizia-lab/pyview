'''
Voronoi translated from Matlab to Python
'''


import numpy as np
from scipy.ndimage import distance_transform_edt
from skimage.morphology import local_maxima, remove_small_objects, label

from .utils import compute_std_projection


def segment_voronoi(movie, min_distance=3, min_size=30):
    """
    Voronoi-based segmentation (CalciSeg style).

    Parameters
    ----------
    movie : ndarray, shape (H, W, T)
        Calcium movie, already loaded into memory.
    min_distance : int
        Minimum distance between detected maxima.
    min_size : int
        Minimum region size in pixels to keep.

    Returns
    -------
    labels : ndarray, shape (H, W)
        Integer-labeled region map (0 = background).
    seeds : ndarray, shape (N, 2)
        Seed coordinates as (row, col).
    """

    H, W, T = movie.shape

    # -------------------------------------------------------
    # 1. STD projection
    # -------------------------------------------------------
    std_img = compute_std_projection(movie)

    # -------------------------------------------------------
    # 2. Find local maxima (binary mask)
    #    skimage local_maxima gives True at peaks
    # -------------------------------------------------------
    maxima_mask = local_maxima(std_img)

    # Extract seed coordinates
    seed_coords = np.column_stack(np.where(maxima_mask))

    if len(seed_coords) == 0:
        return np.zeros((H, W), dtype=int), seed_coords

    # -------------------------------------------------------
    # 3. Voronoi partition via distance transform
    # -------------------------------------------------------
    # Prepare an array marking seed positions with unique IDs
    seed_map = np.zeros((H, W), dtype=int)

    for idx, (r, c) in enumerate(seed_coords):
        seed_map[r, c] = idx + 1  # label seeds starting at 1

    # Distance transform: compute distance to nearest seed
    distances, nearest_seed = distance_transform_edt(
        seed_map == 0,
        return_indices=True
    )

    # nearest_seed gives (coords along axis 0, axis 1)
    nearest_r = nearest_seed[0]
    nearest_c = nearest_seed[1]

    # Map each pixel to the seed ID sitting at that location
    labels = seed_map[nearest_r, nearest_c]

    # -------------------------------------------------------
    # 4. Remove tiny regions
    # -------------------------------------------------------
    labels = _remove_small_regions(labels, min_size=min_size)

    return labels, seed_coords


# -----------------------------------------------------------
# Helper: remove small connected regions
# -----------------------------------------------------------
def _remove_small_regions(label_map, min_size=30):
    """
    Remove objects smaller than min_size.

    Returns
    -------
    cleaned : ndarray
    """
    # skimage remove_small_objects works on boolean or int images
    cleaned = remove_small_objects(label_map, min_size)

    # relabel after removing objects
    cleaned = label(cleaned)

    return cleaned


# simpler version? maybe compare speed later
import numpy as np
from scipy.spatial import cKDTree

def segment_voronoi_simple(image, seeds):
    """
    image: 2D array
    seeds: list of (y, x)

    Returns a label image with same shape.
    """

    X, Y = image.shape
    labels = np.zeros((X, Y), dtype=np.int32)

    pts = np.array(seeds)
    tree = cKDTree(pts)

    yy, xx = np.indices((X, Y))
    coords = np.column_stack((yy.ravel(), xx.ravel()))

    d, idx = tree.query(coords)
    labels[:] = idx.reshape(X, Y)
    
    return labels
