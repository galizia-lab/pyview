import numpy as np
import time
from sklearn.decomposition import PCA, FastICA
from sklearn.linear_model import LinearRegression


def compress_movie_to_projection(movie, method="std"):
    """
    movie: expected shape (T, Y, X)
    """

    if method == "max":
        return np.max(movie, axis=0)

    elif method == "mean":
        return np.mean(movie, axis=0)

    elif method == "std":
        return np.std(movie, axis=0)

    else:
        raise ValueError(f"Unknown projection method: {method}")
    



def compute_ica_projection(
    movie,
    n_components=20,
    mask=None,
    pca_components=None,
    detrend=True,
    proj_method="maxabs",   # options: "maxabs", "sumabs", "sum_squares", "variance_weighted"
    random_state=0,
    verbose=True,
    movie_shape='THW'
):
    """
    Compute an ICA-based 2D projection from a movie (H, W, T).

    Parameters
    ----------
    movie : ndarray
        Array of shape (H, W, T) or (T, H, W). Function will handle either.
    n_components : int
        Number of ICA components to estimate.
    mask : None or (H, W) bool array
        Optional spatial mask. If provided, only pixels where mask==True are used.
    pca_components : None or int
        Number of PCA components to keep before ICA (whitening). If None, uses n_components.
        Use larger than n_components if you want to keep some variance.
    detrend : bool
        If True, remove a linear trend from each pixel timecourse.
    proj_method : str
        How to collapse components into one 2D projection:
          - "maxabs": for each pixel take max over components of abs(spatial_weight * component_energy)
          - "sumabs": sum of absolute weighted spatial weights across components
          - "sum_squares": sum of squared spatial weights (like energy)
          - "variance_weighted": weight spatial maps by temporal source variance then sum abs
    random_state : int
        RNG seed for reproducibility.
    verbose : bool
        Print timing and shape info.

    Returns
    -------
    proj_img : ndarray
        2D array shape (H, W) containing the ICA-based projection.
    ica_result : dict
        Dictionary with keys:
          - 'spatial_maps': (n_components, N_masked) or (n_components, H, W) if mask is None
          - 'temporal_traces': (T, n_components)
          - 'mask': mask used (bool array of shape H,W)
          - 'pca': PCA object (or None)
          - 'ica': FastICA object
    """
    t0 = time.time()

    # --- Accept either (H,W,T) or (T,H,W) ---
    movie = np.asarray(movie)
    if movie.ndim == 3:
        if movie.shape[2] < movie.shape[0] and movie.shape[0] == movie.shape[1]:
            # ambiguous; assume (H,W,T) in typical use. No change.
            pass
        # We want movie of shape (H, W, T)
        if movie.shape[0] != movie.shape[1] and movie.shape[2] < movie.shape[0]:
            # It's possible the movie is (T, H, W) — detect naive case:
            # but safer to accept both, so we check T dimension by seeing typical range
            pass
    else:
        raise ValueError("movie must be 3D array (H, W, T) or (T, H, W)")

    # Try to standardize: if last axis is time, keep (H,W,T), else transpose
    if (movie_shape == 'THW') or (movie_shape == 'TWH'):
        movie = np.transpose(movie, (1, 2, 0))  # to (H, W, T)
    H, W, T = movie.shape
    print(f": {movie.shape}; interpreting as (H, W, T)")

    # --- Build mask ---
    if mask is None:
        mask = np.ones((H, W), dtype=bool)
    else:
        mask = np.asarray(mask, dtype=bool)
        if mask.shape != (H, W):
            raise ValueError("mask must be shape (H, W)")

    pix_idx = np.flatnonzero(mask)
    N_masked = pix_idx.size
    if N_masked == 0:
        raise ValueError("Mask has no True pixels")

    # --- Reshape to (T, N) where N = number of masked pixels ---
    movie_reshaped = movie.reshape(-1, T).T  # -> (T, H*W)
    X = movie_reshaped[:, pix_idx]          # (T, N_masked)

    # --- Optional detrending (remove linear trend per pixel) ---
    if detrend:
        # Subtract linear fit along time for each pixel
        # X shape: (T, N)
        t = np.arange(T).reshape(-1, 1)                  # (T, 1)
        tt = t - t.mean()                                # (T, 1)

        # Compute means per pixel
        mean_X = X.mean(axis=0, keepdims=True)           # (1, N)

        # Numerator: sum_t (t - mean(t)) * (X - mean(X))
        num = (tt * (X - mean_X)).sum(axis=0)            # (N,)

        # Denominator: sum_t (t - mean(t))^2   (scalar)
        den = (tt * tt).sum()

        # Slope per pixel (N,)
        slope = num / den

        # Reconstruct linear trend for each pixel
        trend = slope[np.newaxis, :] * (t - t.mean()) + mean_X

        # Remove trend
        X = X - trend



    # --- Center (zero-mean in time) ---
    X = X - X.mean(axis=0, keepdims=True)

    # --- PCA whitening (dim reduction) ---
    if pca_components is None:
        pca_components = max(n_components, min(T, N_masked, n_components))

    pca_components = int(pca_components)
    if pca_components >= min(T, N_masked):
        pca_obj = None
        X_white = X
        pca_components_used = min(T, N_masked)
    else:
        pca_obj = PCA(n_components=pca_components, whiten=True, svd_solver="randomized", random_state=random_state)
        X_white = pca_obj.fit_transform(X)   # (T, pca_components)
        pca_components_used = pca_components

    # --- Run FastICA ---
    ica = FastICA(n_components=n_components, whiten=False, random_state=random_state, max_iter=500)
    # scikit-learn expects (n_samples, n_features) = (T, pca_components)
    S = ica.fit_transform(X_white)         # (T, n_components) temporal sources
    # components_ has shape (n_components, n_features_in_input)
    comp = ica.components_                 # if pca used: shape (n_components, pca_components)
                                           # else: shape (n_components, N_masked)

    # If PCA was used, recover spatial maps in original pixel-space:
    if pca_obj is not None:
        # pca_obj.components_ shape: (pca_components, N_masked)
        # comp (n_components, pca_components)
        spatial_maps = comp @ pca_obj.components_   # -> (n_components, N_masked)
    else:
        spatial_maps = comp.copy()                  # (n_components, N_masked)

    # Normalize spatial maps (optional)
    # We'll z-score each spatial map to make combination stable
    spatial_maps = spatial_maps - spatial_maps.mean(axis=1, keepdims=True)
    denom = np.linalg.norm(spatial_maps, axis=1, keepdims=True) + 1e-12
    spatial_maps = spatial_maps / denom

    # Compute a weight per component (temporal energy / variance)
    temporal_energy = S.var(axis=0)  # length n_components

    # --- Collapse to single projection image ---
    # Several common aggregation strategies:
    if proj_method == "maxabs":
        # weight spatial maps by temporal energy, then take per-pixel max abs across components
        weighted = np.abs(spatial_maps * temporal_energy[np.newaxis, :].T)  # (n_comp, N)
        agg = weighted.max(axis=0)
    elif proj_method == "sumabs":
        agg = np.abs(spatial_maps * temporal_energy[np.newaxis, :].T).sum(axis=0)
    elif proj_method == "sum_squares":
        agg = (spatial_maps**2).sum(axis=0)
    elif proj_method == "variance_weighted":
        agg = np.abs(spatial_maps).T @ temporal_energy
    else:
        raise ValueError(f"Unknown proj_method {proj_method}")

    # Put back into H,W
    proj_img = np.zeros(H * W, dtype=float)
    proj_img[pix_idx] = agg
    proj_img = proj_img.reshape(H, W)

    # simple normalization for display
    proj_img = proj_img - proj_img.min()
    if proj_img.max() > 0:
        proj_img = proj_img / proj_img.max()

    t_elapsed = time.time() - t0
    if verbose:
        print(f"ICA projection computed: movie {H}x{W}x{T}, mask pixels {N_masked}, "
              f"pca_components={pca_components_used}, ica_components={n_components} -> {t_elapsed:.2f} s")

    ica_result = {
        "spatial_maps": spatial_maps.reshape((spatial_maps.shape[0], -1)),  # (n_components, N_masked)
        "temporal_traces": S,            # (T, n_components)
        "mask": mask,
        "pca": pca_obj,
        "ica": ica,
    }

    return proj_img, ica_result

