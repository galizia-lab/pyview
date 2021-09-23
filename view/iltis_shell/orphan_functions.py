from view.python_core.rois.iltis_rois.text_based import CircleILTISROIData, PolygonILTISROIData
from iltis.Objects.ROIs_Object import myPolyLineROI, myCircleROI


def convert_iltisROI2VIEWROI(roi):

    if type(roi) == myCircleROI:
                    roi_data = CircleILTISROIData(label=roi.label, x=roi.center[0], y=roi.center[1], d=roi.diameter)
    elif type(roi) == myPolyLineROI:
        # copied from ILTIS
        handle_pos = [tup[1] for tup in roi.getSceneHandlePositions()]
        pos_mapped = [roi.ViewBox.mapToView(pos) for pos in handle_pos]
        roi_data = PolygonILTISROIData(label=roi.label,
                                       list_of_vertices=[(pos.x(), pos.y()) for pos in pos_mapped])
    else:
        raise NotImplementedError

    return roi_data
