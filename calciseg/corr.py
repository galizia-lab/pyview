import time
from tracemalloc import start
from networkx import radius
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

def find_correlation_peaks(corr_map, 
                           min_distance=flags.CS_seed_min_distance, 
                           threshold_rel=0.05,
                           threshold_abs= flags.CS_max_threshold,
                           sigma=flags.CS_seed_min_distance/2):

    """
    Returns list of (x, y) seed coordinates.
    Based on local maxima of correlation map.
    """
    smoothed = gaussian_filter(corr_map, sigma=sigma)

    peaks = peak_local_max(
        smoothed,
        min_distance=min_distance,
        threshold_rel=threshold_rel,
        threshold_abs=threshold_abs,
        exclude_border=False
    )
    return [tuple(p) for p in peaks]   # list of (x, y)


# -----------------------------------------------------------
# 4) CORRELATION-DRIVEN REGION GROWING
# -----------------------------------------------------------

def extract_patch(data, y, x, radius):
    """
    data: (H, W, T) no: data is (T, H, W)
    seed at (y, x)
    returns:
        patch: (h, w, T)
        y0, x0: top-left corner in global coords
    """
    _, H, W = data.shape

    y0 = max(0, y - radius)
    y1 = min(H, y + radius + 1)
    x0 = max(0, x - radius)
    x1 = min(W, x + radius + 1)

    patch = data[: ,y0:y1, x0:x1]

    return patch, y0, x0

def circular_mask(h, w, cy, cx, radius):
    yy, xx = np.ogrid[:h, :w]
    return (yy - cy)**2 + (xx - cx)**2 <= radius**2


def local_correlation_map(patch, seed_trace):
    """
    patch: (T, h, w)
    seed_trace: (T,)
    returns: (h, w) correlation map
    """
    T, h, w = patch.shape

    # Move time axis to the end: (h, w, T)
    # patch_hwT = np.transpose(patch, (1, 2, 0))
    # Reshape pixels → (N, T)
    # X = patch_hwT.reshape(-1, T)
    # alternatively, make contiguous first only if needed for memory layout:
    X = np.ascontiguousarray(
            patch.transpose(1, 2, 0)
        ).reshape(-1, T)


    # Normalize
    X = X - X.mean(axis=1, keepdims=True)
    seed = seed_trace - seed_trace.mean()

    # Correlation
    denom = np.linalg.norm(X, axis=1) * np.linalg.norm(seed)
    corr = (X @ seed) / (denom + 1e-8)

    return corr.reshape(h, w)


def grow_local_region(seed_hw, corr_map, 
                threshold=flags.CS_corr_threshold,
                glo_radius=flags.CS_corr_circle_radius,
                mask_circle=True):
    """
    Region growing starting from seed (x, y)
    by adding neighboring pixels with correlation > threshold.

    Returns mask of this ROI.
    """
    H, W = corr_map.shape
    mask = np.zeros((H, W), dtype=bool)

    sh, sw = seed_hw
    frontier = [(sh, sw)]
    mask[sh, sw] = True

    if mask_circle:
        mask_circle = circular_mask(H, W, sh, sw, glo_radius)

    while frontier:
        h, w = frontier.pop()
        # check neighbors
        for nh in (h - 1, h, h + 1):
            for nw in (w - 1, w, w + 1):
                if nh < 0 or nw < 0 or nh >= H or nw >= W:
                    continue
                if not mask_circle[nh, nw]:
                    continue
                if mask[nh, nw]:
                    continue
                if corr_map[nh, nw] > threshold:
                    mask[nh, nw] = True
                    frontier.append((nh, nw))

    return mask



def grow_global_region(seed_hw, corr_global, data,
                threshold=flags.CS_corr_threshold,
                glo_radius=flags.CS_corr_circle_radius):
    """
    Region growing starting from seed (x, y)
    by adding neighboring pixels with correlation > threshold.

    Returns mask of this ROI.
    """
    sh, sw = seed_hw
    patch, h0, w0 = extract_patch(data, sh, sw, glo_radius)
    seed_trace = data[:, sh, sw]

    corr_local = local_correlation_map(patch, seed_trace)

    local_mask = grow_local_region(
            seed_hw=(sh - h0, sw - w0), corr_map=corr_local,
            threshold=threshold)
    # copy into global mask
    H, W = corr_global.shape
    global_mask = np.zeros((H, W), dtype=bool)
    global_mask[h0:h0+local_mask.shape[0],
                w0:w0+local_mask.shape[1]] = local_mask
    
    return global_mask



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
    print(f"computed correlation. It took {time.time() - start:.2f} seconds")
    
    seeds = find_correlation_peaks(corr_map)
    print(f"together with find peaks took {time.time() - start:.2f} seconds")
    
    rois = []
    for s in seeds:
        roi = grow_global_region(s, corr_map, movie, threshold=corr_threshold)
        rois.append(roi)

    rois = merge_overlapping_rois(rois)
    print(f"together with rois {time.time() - start:.2f} seconds")
    

    return corr_map, seeds, rois
