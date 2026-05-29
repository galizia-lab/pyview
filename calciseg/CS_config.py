# CS_config.py

from dataclasses import dataclass

@dataclass
class Config:
    """
    Global configuration for the project.
    Add new parameters here as needed.
    """
    CS_proj_method: str = "local_corr"
    # values: 'mean', 'max', 'std', 'global_corr', 'local_corr', 'ica'
    CS_corr_threshold: float = 0.6
    CS_corr_circle_radius: int = 20 # approx glo radius in pixels
    CS_seed_min_distance: int = 10
    # set threshold for local maxima-based segmentation
    CS_max_threshold = 0.2
    # for proj_method 'max', z_transform should be False
    CS_z_transform: bool = False
    # how is the 3D movie array shaped
    CS_movie_shape: str = 'THW' #'HWT'  # 'HWT' or 'THW' 


# Create a single global instance
config = Config()

