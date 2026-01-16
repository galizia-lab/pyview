# CS_config.py

from dataclasses import dataclass

@dataclass
class Config:
    """
    Global configuration for the project.
    Add new parameters here as needed.
    """
    CS_proj_method: str = "ica"
    # values: 'mean', 'max', 'std', 'global_corr', 'local_corr', 'ica'
    CS_corr_threshold: float = 0.4
    CS_corr_circle_radius: int = 5
    CS_seed_min_distance: int = 5
    CS_z_transform: bool = True
    # how is the 3D movie array shaped
    CS_movie_shape: str = 'THW' #'HWT'  # 'HWT' or 'THW' 


# Create a single global instance
config = Config()

