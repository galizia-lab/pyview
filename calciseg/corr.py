import time
from tracemalloc import start
import numpy as np
from scipy.ndimage import gaussian_filter, binary_dilation, generate_binary_structure
from skimage.feature import peak_local_max

from calciseg.CS_config import config as flags  # import global config


# -----------------------------------------------------------
# 1) PIXEL TRACE EXTRACTION
# -----------------------------------------------------------

def extract_traces(movie):
    """
    movie: 3D numpy array (T, X, Y)
    returns traces: (X*Y, T) flattened pixel traces
            and shape: (X, Y)
    """
    T, X, Y = movie.shape
    traces = movie.reshape(T, X * Y).T  # (pixels, time)
    return traces, (X, Y)


# -----------------------------------------------------------
# 2) GLOBAL CORRELATION MAP
# -----------------------------------------------------------

def compute_correlation_map(traces, shape):
    """
    Compute per-pixel correlation with global median trace.
    Equivalent to CalciSeg "CorrMap".
    """
    global_trace = np.median(traces, axis=0)

    # Normalize
    traces_norm = traces - traces.mean(axis=1, keepdims=True)
    global_norm = global_trace - global_trace.mean()
    global_norm /= np.linalg.norm(global_norm) + 1e-12

    # Dot product = correlation
    corr = traces_norm @ global_norm
    corr /= np.linalg.norm(traces_norm, axis=1) + 1e-12

    return corr.reshape(shape)

# -----------------------------------------------------------
# 2) Alternatively:  LOCAL CORRELATION MAP
# -----------------------------------------------------------

def compute_local_correlation_map(traces, shape, circle_radius):
    """
    Compute per-pixel correlation between each pixel's trace and the average
    trace of all pixels within a circular neighborhood.

    traces: (N_pixels, T)
    shape: (H, W)
    circle_radius: radius in pixels
    """
    H, W = shape
    N, T = traces.shape

    # ---- 1. Precompute circular offsets ----
    r = circle_radius
    ys, xs = np.mgrid[-r:r+1, -r:r+1]
    mask = xs**2 + ys**2 <= r**2
    offsets = np.column_stack((ys[mask], xs[mask]))  # (K, 2)

    # ---- 2. Build neighbor lists for each pixel ----
    # Preallocate list of arrays of indices
    neighbor_lists = []
    for idx in range(N):
        y = idx // W
        x = idx % W

        coords = offsets + np.array([y, x])
        # keep only in-bounds coordinates
        valid = (coords[:, 0] >= 0) & (coords[:, 0] < H) & \
                (coords[:, 1] >= 0) & (coords[:, 1] < W)
        coords = coords[valid]

        # convert coords → linear indices
        nbr_idx = coords[:, 0] * W + coords[:, 1]
        neighbor_lists.append(nbr_idx)

    # ---- 3. Compute each pixel’s local-mean trace ----
    local_mean = np.zeros_like(traces)
    for i, nbr_idx in enumerate(neighbor_lists):
        local_mean[i] = traces[nbr_idx].mean(axis=0)

    # ---- 4. Normalize pixel traces & local-means ----
    traces_norm = traces - traces.mean(axis=1, keepdims=True)
    local_norm = local_mean - local_mean.mean(axis=1, keepdims=True)

    # Avoid divide-by-zero
    denomA = np.linalg.norm(traces_norm, axis=1) + 1e-12
    denomB = np.linalg.norm(local_norm, axis=1) + 1e-12

    # ---- 5. Compute correlation ----
    corr = np.sum(traces_norm * local_norm, axis=1) / (denomA * denomB)

    return corr.reshape(shape)

# -----------------------------------------------------------
# 3) LOCAL MAXIMA DETECTION (SEEDS)
# -----------------------------------------------------------

def find_correlation_peaks(corr_map, min_distance=flags.CS_seed_min_distance, 
                           threshold_rel=0.05):
    """
    Returns list of (x, y) seed coordinates.
    Based on local maxima of correlation map.
    """
    smoothed = gaussian_filter(corr_map, sigma=1.0)

    peaks = peak_local_max(
        smoothed,
        min_distance=min_distance,
        threshold_rel=threshold_rel,
        exclude_border=False
    )
    return [tuple(p) for p in peaks]   # list of (x, y)


# -----------------------------------------------------------
# 4) CORRELATION-DRIVEN REGION GROWING
# -----------------------------------------------------------

def grow_region(seed_xy, corr_map, threshold=0.4):
    """
    Region growing starting from seed (x, y)
    by adding neighboring pixels with correlation > threshold.

    Returns mask of this ROI.
    """
    X, Y = corr_map.shape
    mask = np.zeros((X, Y), dtype=bool)

    sx, sy = seed_xy
    frontier = [(sx, sy)]
    mask[sx, sy] = True

    neigh = generate_binary_structure(2, 1)

    while frontier:
        x, y = frontier.pop()
        # check neighbors
        for nx in (x - 1, x, x + 1):
            for ny in (y - 1, y, y + 1):
                if nx < 0 or ny < 0 or nx >= X or ny >= Y:
                    continue
                if mask[nx, ny]:
                    continue
                if corr_map[nx, ny] > threshold:
                    mask[nx, ny] = True
                    frontier.append((nx, ny))

    return mask


# -----------------------------------------------------------
# 5) MERGING REGIONS
# -----------------------------------------------------------

def merge_overlapping_rois(rois, min_overlap=0.3):
    """
    Merge ROIs that overlap strongly.
    rois = list of boolean masks

    Returns merged list.
    """
    merged = []
    used = [False] * len(rois)

    for i in range(len(rois)):
        if used[i]:
            continue

        base = rois[i].copy()
        used[i] = True

        for j in range(i + 1, len(rois)):
            if used[j]:
                continue

            overlap = np.sum(base & rois[j]) / np.sum(rois[j])
            if overlap > min_overlap:
                base |= rois[j]
                used[j] = True

        merged.append(base)

    return merged


# -----------------------------------------------------------
# 6) MAIN PIPELINE
# -----------------------------------------------------------

def run_correlation_segmentation(movie):
    """
    Full correlation-based segmentation pipeline.
    Input movie: 3D numpy array (T, X, Y)
    Returns list of ROI masks.
    """
    corr_threshold = flags.CS_corr_threshold
    traces, shape = extract_traces(movie)

    start = time.time()
    if flags.CS_proj_method == 'global_corr':
        corr_map = compute_correlation_map(traces, shape)
    elif flags.CS_proj_method == 'local_corr':
        corr_map = compute_local_correlation_map(
            traces, shape, circle_radius=flags.CS_corr_circle_radius)
    print(f"compute correlation took {time.time() - start:.2f} seconds")
    seeds = find_correlation_peaks(corr_map)
    print(f"together with find peaks took {time.time() - start:.2f} seconds")
    
    rois = []
    for s in seeds:
        roi = grow_region(s, corr_map, threshold=corr_threshold)
        rois.append(roi)

    rois = merge_overlapping_rois(rois)
    print(f"together with rois {time.time() - start:.2f} seconds")
    

    return corr_map, seeds, rois
