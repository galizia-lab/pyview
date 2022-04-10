import numpy as np
from view.idl_translation_core.bleach_correction import fitlogdecay, model_func
from itertools import product
import multiprocessing as mp
import logging
import platform


shared_arr_g = None
patch_size_g = None


def _init(shared_arr_, patch_size_, weights_, fit_pars_dict_):
    # The shared array pointer is a global variable so that it can be accessed by the
    # child processes. It is a tuple (pointer, dtype, shape).
    global shared_arr, patch_size, weights, fit_pars_dict
    shared_arr = shared_arr_
    patch_size = patch_size_
    weights = weights_
    fit_pars_dict = fit_pars_dict_


def shared_to_numpy(shared_array_pars, copy=False):
    """Get a NumPy array from a shared memory buffer, with a given dtype and shape.
    No copy is involved, the array reflects the underlying shared buffer."""
    shared_arr, dtype, shape = shared_array_pars
    wrapped_arr = np.frombuffer(shared_arr, dtype=dtype).reshape(shape)
    if copy:
        copy_arr = np.empty_like(wrapped_arr)
        np.copyto(dst=copy_arr, src=wrapped_arr)
        return copy_arr
    else:
        return wrapped_arr


def numpy2raw_array(ndarray):
    """
    Convert numpy array to raw array
    """
    dtype = ndarray.dtype
    shape = ndarray.shape
    # Get a ctype type from the NumPy dtype.
    cdtype = np.ctypeslib.as_ctypes_type(dtype)
    # Create the RawArray instance.
    shared_arr = mp.RawArray(cdtype, int(np.prod(shape)))
    # Wrap shared_arr as an numpy array so we can easily manipulates its data (here only to copy data into it)
    fake_numpy_arr = shared_to_numpy((shared_arr, dtype, shape))

    np.copyto(dst=fake_numpy_arr, src=ndarray)

    return shared_arr, dtype, shape


def bleach_correct_pixelwise(movie: np.ndarray, weights, area, ncpu: int):

    assert movie.shape[:2] == area.shape, f"Area file specified has dimensions {area.shape} that does not match with" \
                                          f"data dimensions {movie.shape}"

    pixel_inds = [ind for ind, val in np.ndenumerate(area) if val]

    global shared_arr_g, weights_g

    # mmappickle could be used instead of shared memory. https://mmappickle.readthedocs.io/en/latest/
    shared_arr_g = numpy2raw_array(movie)
    weights_g = weights

    if ncpu > 1:

        assert platform.system() != "Windows", \
            "Pixelwise bleach correction currently does not work on Windows due to parallization issues. Sorry!"

        # apply bleach correction to each patch in parallel
        with mp.Pool(processes=ncpu) as p:  # use all cores
            op_params_list = p.map(bleach_correct_pixelwise_worker, pixel_inds, chunksize=100)
    elif ncpu == 1:

        # apply bleach correction to each patch without parallelization
        op_params_list = []
        for pixel_ind_nr, pixel_ind in enumerate(pixel_inds):
            logging.getLogger("VIEW").debug(f"Doing pixel {pixel_ind_nr + 1}/{len(pixel_inds)}")
            op_params = bleach_correct_pixelwise_worker(pixel_ind)
            op_params_list.append(op_params)
    else:
        raise ValueError(f"Paramater ncpu has to be 1 or more ({ncpu} specified)")

    array2return = shared_to_numpy(shared_arr_g, copy=True)

    return array2return, {k: v for k, v in zip(pixel_inds, op_params_list)}


def bleach_correct_pixelwise_worker(pixel_index: tuple):

    movie = shared_to_numpy(shared_arr_g)

    # reduce patch to curve
    curve = movie[pixel_index[0], pixel_index[1], :]

    # apply bleach correction to curve and return the parameters A, K and C
    fitted_curve, (A, K, C) = fitlogdecay(lineIn=curve, weights=weights_g, showresults=False)

    # sometimes A and/or K can be NAN, then don't bleach correct
    # adding the mean of the fitted curve ensures the average intensity value of every pixel
    # is not affected by the bleach correction applied
    if not np.isnan(A) and not np.isnan(K):
        movie[pixel_index[0], pixel_index[1], :] = curve - fitted_curve + fitted_curve.mean()

    return A, K, C
