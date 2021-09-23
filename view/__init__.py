from pkg_resources import get_distribution

__version__ = get_distribution(__name__).version

from .python_core.view_object import VIEW
from .python_core.tapestries import create_tapestry



