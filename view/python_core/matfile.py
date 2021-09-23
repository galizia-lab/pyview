from scipy.io import savemat
from view.python_core.get_internal_files import get_gdm_doc_df
from view.python_core.p1_class import P1SingleWavelengthTIF
from view.python_core.flags import FlagsManager
from view.python_core.gdm_generation.glomeruli_managers import get_gdm_row_boiler_plate_sans_glo
import numpy as np


def export_processed_data_as_mat_file(view_object, analyze_values_to_use):

    # initialize measus to use
    measus = view_object.get_measus_for_current_animal(analyze_values_to_use=analyze_values_to_use)

    metadatas = []
    response_frames = []
    signal_movies = []

    # iterate over measurements of the animal
    for measu in measus:
        # load a measurement for the animal
        view_object.load_measurement_data_from_current_animal(measu)

        # calculate signals
        view_object.calculate_signals()

        # accumulate metadata
        metadatas.append(get_gdm_row_boiler_plate_sans_glo(flags=view_object.flags, p1=view_object.p1))

        # accumulate CTV overview
        response_frames.append(view_object.generate_ctv_response_frame_for_current_measurement())

        # accumulate signal
        signal_movies.append(view_object.p1.sig1)

    # convert accumulated data in an numpy array mimicking a MATLAB cell array
    if metadatas:
        n_metadata = len(metadatas[0])
        cell_array = np.empty((len(measus), n_metadata + 2), dtype=object)

        doc_string_cell_array = create_mat_file_doc_string(
            columns=metadatas[0].keys(),
            extra_doc=[
                "response frame as a 2D array. Format XY. "
                "Pixel value indicates response strength as indicated by CTV flags",
                "movie of calcium estimate (ratio or dff) as a 3D array. Format XYT"
            ])

        doc_string = "Variable 'area_mask': 2D logical array, with pixels to be excluded set to False. " \
                     "Will be NaN if an area mask (.AREA file) was not created for this animal\n\n" \
                     "Variable 'GDM': 2D cell array of metadata and data. Column are described below:\n\n" \
                     + doc_string_cell_array

        for measu_ind, measu in enumerate(measus):
            for ind, metadata_val in enumerate(metadatas[measu_ind].values):
                cell_array[measu_ind, ind] = metadata_val

            # flip Y axis as it is output format that is more common
            cell_array[measu_ind, n_metadata] = np.flip(response_frames[measu_ind], axis=1)
            cell_array[measu_ind, n_metadata + 1] = np.flip(signal_movies[measu_ind], axis=1)
    else:
        doc_string = "This file contains no data!"
        cell_array = np.array([])

    area_mask = view_object.p1.area_mask

    op_dir = view_object.flags.get_processed_data_op_path(format_name="MAT")
    op_dir.mkdir(exist_ok=True, parents=True)
    op_file = op_dir / f"{view_object.get_current_animal()}.mat"
    savemat(
        file_name=op_file,
        mdict={
            "doc_string": doc_string,
            "GDM": cell_array,
            "area_mask": area_mask
        },
        do_compression=True)


def create_mat_file_doc_string(columns, extra_doc):
    """
    Creates a string explaining how to interpret data in the cell array of a mat file
    :param Sequence columns: columns of GDM used
    :param Sequence extra_doc: documentation of non-GDM columns in cell array
    :return: str
    """

    gdm_doc_df = get_gdm_doc_df().set_index("Column name")
    doc_str = "\n".join(
        f"Column {ind + 1}: {gdm_doc_df.loc[col_name, 'Description']}" for ind, col_name in enumerate(columns))
    doc_str += "\n" + "\n".join(f"Column {len(columns) + ind + 1}: {val}" for ind, val in enumerate(extra_doc))
    return doc_str