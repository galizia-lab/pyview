'''
Perform glomerular segmentation. 
Based on Jannick Günzel's CalciSeg

- todo
add local correlation-based segmentation option
add ICA-based segmentation option
insert into a pipeline with pyCalciView
externalize parameters (thresholds, etc.) and flag options

'''



import numpy as np
import matplotlib.pyplot as plt

from calciseg.io import load_movie_via_dialog
from calciseg.compress import compress_movie_to_projection, compute_ica_projection   # you will create this
from calciseg.localmax import find_local_maxima, segment_watershed_cells               # also create
from calciseg.voronoi import segment_voronoi, segment_voronoi_simple                  # already discussed
import calciseg.utils as util # import rois_to_label_image, save_label_image, save_roi_list    # optional helpers
from calciseg.corr import run_correlation_segmentation
        
##flags.
from calciseg.CS_config import config as CS_config



def compress_voronoi(movie, method='mean'):
    """
    Full pipeline: compress movie, find local maxima, Voronoi segmentation.

    Parameters
    ----------
    movie : ndarray, shape (H, W, T)

    Returns
    -------
    labels : ndarray, shape (H, W)
        Integer-labeled region map (0 = background).
    seeds : ndarray, shape (N, 2)
        Seed coordinates as (row, col).
    """

    # 1. Compress movie to projection
    proj = compress_movie_to_projection(movie, method=method)

    # 2. Find local maxima
    seeds = find_local_maxima(proj)

    # 3. Voronoi segmentation
    labels = segment_voronoi_simple(proj, seeds)

    return proj, labels, seeds


def main():

    print("=== PyCalciSeg ===")

    # 1) Ask for TIFF file
    movie, meta, input_file = load_movie_via_dialog()
    if movie is None:
        print("No file selected. Exiting.")
        return
    print(f"Loaded movie with shape {movie.shape}")

    # Z-scale movie for better contrast
    if CS_config.CS_z_transform:    
        movie = util.z_scale_movie(movie)

    # 2. Compress movie to projection and calculate seeds and segmentation

    if CS_config.CS_proj_method in ['mean', 'max', 'std']:
        print(f"Using projection method: {CS_config.CS_proj_method}")
         # 2) Run segmentation pipeline, type 1. 
        proj, labels, seeds = compress_voronoi(movie, 
                                               method=CS_config.CS_proj_method)

    elif CS_config.CS_proj_method in ['global_corr', 'local_corr']:
        print("Using correlation-based segmentation. Wait a sec...")
         # 2) Run segmentation pipeline, type 2. 
        proj, seeds, rois = run_correlation_segmentation(movie)


    elif CS_config.CS_proj_method == 'ica':
        print("Using ICA-based projection for segmentation.")
        proj, ica_result = compute_ica_projection(movie, n_components=20, 
                                                  movie_shape=CS_config.CS_movie_shape)
        #seeds = find_local_maxima(proj)
        centers, labels_filtered = segment_watershed_cells(proj)
        seeds = [tuple(p) for p in centers]
        #labels = segment_voronoi_simple(proj, seeds)

    print(f"Projection shape: {proj.shape}")

    # Display projection
    plt.figure(figsize=(6, 6))
    plt.imshow(proj, cmap='gray')
    plt.title("Projection image (for peak detection)")
    plt.axis('off')
    plt.show()

 
    # Optionally show seed overlay
    plt.figure(figsize=(6, 6))
    plt.imshow(proj, cmap='gray')
    ys, xs = zip(*seeds)
    plt.scatter(xs, ys, s=15, edgecolor='red', facecolor='none')
    plt.title("Local maxima (ROI seeds)")
    plt.axis('off')
    plt.show()

    # show segmentation only if 'rois' is defined
    try:
        rois
    except NameError:
        pass
    else:   
        mask_sum = np.sum(np.stack(rois), axis=0)
        plt.imshow(mask_sum > 0, cmap="gray")   
        plt.title("Correlation-based ROIs")
        plt.show()



    # show segmentation only if 'labels' is defined
    try:
        labels
    except NameError:
        X, Y = proj.shape
        labels = util.rois_to_label_image(rois)
        #colored = label_image_to_color(labels)
    plt.figure(figsize=(6, 6))
    plt.imshow(labels, cmap='tab20')
    plt.title("Segmentation Result")
    plt.axis('off')
    plt.show()


    # 5) Save outputs
    print("Saving segmentation results...")

    # save labels to file
    label_file = input_file.replace('.tif', '_labels.tif')
    util.save_label_image(labels, label_file)
    # roi list
    roi_file = input_file.replace('.tif', '_roi_list.csv')
    util.save_roi_list(seeds, roi_file)

    print("Done! Outputs saved as:")
    print("  - segmentation_labels.tif")
    print("  - roi_list.csv")


if __name__ == "__main__":
    main()

'''
From ChatGPT: 6. Dec 2025:
The watershed-based segmentation workflow I provided is not from a single paper, but is a combination of several widely used, standard image-processing techniques that have been used for decades in microscopy and biomedical imaging.
If you want to cite the classical sources for each stage of the pipeline, here are the correct citations:
✔️ 1. Watershed Transform (core method)
This is the standard citation for watershed segmentation in image processing:
Vincent, L., & Soille, P. (1991).
Watersheds in digital spaces: An efficient algorithm based on immersion simulations.
IEEE Transactions on Pattern Analysis and Machine Intelligence, 13(6), 583–598.
This is the canonical reference for the watershed algorithm.
✔️ 2. Distance Transform for Marker-Based Watershed
The distance transform is the basis for blob segmentation:
Felzenszwalb, P. F., & Huttenlocher, D. P. (2012).
Distance transforms of sampled functions.
Theory of Computing, 8(1), 415–428.
✔️ 3. Marker-Controlled Watershed (Maxima → Markers)
A standard review paper used to justify the marker-based strategy:
Beare, R. (2006).
A locally optimal hexagonal grid for image processing.
Computer Vision and Image Understanding, 102(2), 187–194.
Or, alternatively, another excellent reference:
Soille, P. (2003).
Morphological Image Analysis: Principles and Applications.
Springer.
✔️ 4. Local Maxima Detection (max filtering)
This method is based on classical morphological reconstruction:
Meyer, F. (1994).
Topographic distance and watershed lines.
Signal Processing, 38(1), 113–125.
✔️ 5. If you prefer to cite a practical software library
If your method uses scikit-image, appropriate citation:
van der Walt, S., Schönberger, J. L., Nunez-Iglesias, J., et al. (2014).
scikit-image: image processing in Python.
PeerJ, 2:e453.
✔️ Suggested Combined Citation (simple + practical)
If you want a single compact citation for the entire method, use this one:
Vincent, L., & Soille, P. (1991). Watersheds in digital spaces. IEEE PAMI, 13(6), 583–598.
van der Walt, S. et al. (2014). scikit-image: image processing in Python. PeerJ, 2:e453.
These cover:
the watershed algorithm
the fact you implemented it using the standard scikit-image ecosystem
✔️ If you want a citation specifically for calcium-imaging segmentation
Two popular papers using watershed-like or marker-based segmentation:
Mukamel, E. A., Nimmerjahn, A., & Schnitzer, M. J. (2009).
Automated cell body detection and segmentation in calcium imaging data.
Neuron, 63(6), 747–760.
or
Apthorpe, N., Riordan, A. J., Aguilar, R., et al. (2012).
Automatic neuron detection in calcium imaging data.
Frontiers in Neuroinformatics, 6:20.



'''
