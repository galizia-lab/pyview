from calciseg.CS_config import config as flags
import numpy as np
from scipy.ndimage import gaussian_filter, maximum_filter, label, distance_transform_edt
from skimage.segmentation import watershed
from skimage.feature import peak_local_max
from skimage.measure import regionprops

def find_local_maxima(proj, 
                      sigma       =flags.CS_seed_min_distance/2, 
                      min_distance=flags.CS_seed_min_distance, 
                      threshold   =flags.CS_max_threshold):
    """
    Returns list of (y, x) coordinates.
    Smoothing should be related to expected cell size.
    """
    # thresholding only makes sense if range is known. Scale to [0, 1]
    proj_min = proj.min()
    proj_max = proj.max()
    if proj_max > proj_min:
        proj = (proj - proj_min) / (proj_max - proj_min)
    else:
        proj = proj - proj_min  # all pixels same value

    # smooth a bit
    smoothed = gaussian_filter(proj, sigma=sigma)

    # get local maxima
    neigh = (maximum_filter(smoothed, size=min_distance*2+1) == smoothed)

    # threshold away low-intensity peaks
    # thresholding only makes sense if range is known. Scale to [0, 1]
    smoothed_min = smoothed.min()
    smoothed_max = smoothed.max()
    if smoothed_max > smoothed_min:
        smoothed = (smoothed - smoothed_min) / (smoothed_max - smoothed_min)
    else:
        smoothed = smoothed - smoothed_min  # all pixels same value
    neigh &= (smoothed > threshold)

    ys, xs = np.where(neigh)

    return list(zip(ys, xs))



import numpy as np
from scipy.ndimage import gaussian_filter, maximum_filter, label, distance_transform_edt
from skimage.segmentation import watershed
from skimage.morphology import remove_small_objects
from skimage.measure import regionprops

def segment_watershed_cells(
    img,
    min_diameter=10,
    max_diameter=50,
    smoothing_sigma=2.0,
    local_max_window=15,
    threshold_rel=0.1,
    verbose=True
):
    """
    Watershed segmentation for blob-like objects in a 2D projection.
    Compatible with scikit-image 0.25.2 (no use of peak_local_max indices kwarg).

    Parameters
    ----------
    img : 2-D ndarray (H, W)
        Projection image (float or int)
    min_diameter, max_diameter : int
        Expected cell diameter range (pixels).
    smoothing_sigma : float
        Gaussian smoothing sigma to suppress noise.
    local_max_window : int
        Window size for local maxima detection (approx ~radius).
    threshold_rel : float
        Relative threshold (fraction of max) to ignore very dim regions.
    verbose : bool
        Print progress messages.

    Returns
    -------
    centers : list of (y, x) floats
        Centroids of accepted regions.
    labels_filtered : 2-D ndarray (H, W) int
        Labeled segmentation mask (0 = background).
    """
    # 0) basic checks
    if img.ndim != 2:
        raise ValueError("img must be 2D (H, W)")

    H, W = img.shape
    if verbose: print("segment_watershed_cells: Input image:", img.shape)

    # 1) Smooth
    if verbose: print("segment_watershed_cells: Smoothing (sigma=%.2f)..." % smoothing_sigma)
    img_smooth = gaussian_filter(img, sigma=smoothing_sigma)

    # 2) Threshold to get a rough foreground mask
    thr = threshold_rel * img_smooth.max()
    if verbose: print("segment_watershed_cells: Thresholding at", thr)
    mask = img_smooth > thr

    # If mask is empty fall back to small threshold
    if mask.sum() == 0:
        if verbose: print("Warning: threshold removed everything; lowering threshold.")
        thr = max(0.01 * img_smooth.max(), img_smooth.max() * 0.001)
        mask = img_smooth > thr

    # 3) Distance transform (works on binary mask)
    if verbose: print("segment_watershed_cells: Distance transform...")
    dist = distance_transform_edt(mask)

    # 4) Local maxima detection using maximum_filter (avoids peak_local_max indices kwarg)
    if verbose: print("segment_watershed_cells: Local maxima detection using maximum_filter (window=%d)..." % local_max_window)
    if local_max_window <= 1:
        footprint = np.ones((1, 1), dtype=bool)
    else:
        footprint = np.ones((local_max_window, local_max_window), dtype=bool)

    local_max_mask = (dist == maximum_filter(dist, footprint=footprint)) & (dist > 0)

    # Optionally remove any maxima outside the mask or that are too small in distance
    # e.g., only keep maxima with distance >= min_radius/2
    min_radius = min_diameter / 2.0
    local_max_mask &= (dist >= (min_radius * 0.5))  # tweakable

    # Label the maxima to create integer markers
    if verbose: print("segment_watershed_cells: Labeling local maxima -> markers")
    markers, n_markers = label(local_max_mask)
    if verbose: print("segment_watershed_cells: Initial markers:", n_markers)

    # If no markers found, relax criteria: use maxima of smoothed image
    if n_markers == 0:
        if verbose: print("segment_watershed_cells: No maxima found in dist map; falling back to image maxima")
        raw_local = (img_smooth == maximum_filter(img_smooth, footprint=footprint)) & (img_smooth > thr)
        markers, n_markers = label(raw_local)
        if verbose: print("segment_watershed_cells: Fallback markers:", n_markers)
        if n_markers == 0:
            if verbose: print("segment_watershed_cells: Still no markers found; returning empty result")
            return [], np.zeros_like(img, dtype=int)

    # 5) Watershed on negated distance with markers
    if verbose: print("segment_watershed_cells: Running watershed (markers=%d)..." % n_markers)
    labels_ws = watershed(-dist, markers=markers, mask=mask)

    # 6) Filter regions by area (min/max diameter -> min/max area)
    min_area = np.pi * (min_diameter / 2.0) ** 2
    max_area = np.pi * (max_diameter / 2.0) ** 2
    if verbose:
        print(f"segment_watershed_cells: Filtering regions by area: min_area={min_area:.1f}, max_area={max_area:.1f}")

    labels_filtered = np.zeros_like(labels_ws, dtype=int)
    next_label = 1
    centers = []

    for region in regionprops(labels_ws, intensity_image=img_smooth):
        a = region.area
        if a < min_area or a > max_area:
            continue
        # keep region
        coords = region.coords
        labels_filtered[coords[:, 0], coords[:, 1]] = next_label
        centers.append(region.centroid)  # (y, x) as float
        next_label += 1

    if verbose: print(f"segment_watershed_cells: Kept {len(centers)} regions after area filtering")

    return centers, labels_filtered
