import napari
import numpy as np
import pandas as pd
from magicgui import magicgui

def napari_circle_roi_picker(image):
    viewer = napari.Viewer()
    viewer.add_image(image, name="projection", colormap="gray")

    # Shapes layer for circle ROIs
    shapes = viewer.add_shapes(
        name="ROIs",
        shape_type="ellipse",
        edge_color="red",
        face_color="transparent",
        edge_width=2
    )

    # ---- Export button ----
    @magicgui(call_button="Export ROIs", filename={"label": "Output file"})
    def export_rois(filename: str = "rois.txt"):
        records = []

        for i, shape in enumerate(shapes.data):
            # shape is Nx2 array; ellipse defined by bounding box
            y = shape[:, 0]
            x = shape[:, 1]

            x_center = x.mean()
            y_center = y.mean()
            diameter = max(x.max() - x.min(), y.max() - y.min())

            records.append({
                "name": f"circle {i+1}",
                "x": x_center,
                "y": y_center,
                "diameter": diameter
            })

        df = pd.DataFrame(records)
        df.to_csv(filename, sep="\t", index=False)
        print(f"Saved {len(df)} ROIs to {filename}")

    viewer.window.add_dock_widget(export_rois, area="right")

    napari.run()


# some code to do debugging. Will not be used when loaded as library
def debug_manual_circle_roi_picker():
    # Example projection image
    image = np.random.rand(256, 256)

    napari_circle_roi_picker(image)

    


if __name__ == "__main__":
    debug_manual_circle_roi_picker()
