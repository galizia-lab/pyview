import pprint

from view.gui.application_settings import initialize_app_settings
from view.gui.flags_search import get_flags_index, query
from view.python_core.flags import FlagsManager


def test_index_creation():
    """
    Testing creation of flags index
    """

    initialize_app_settings()
    flags = FlagsManager()

    ix = get_flags_index(flags)
    return ix


def test_querys():
    """
    Testing querying index
    """
    ix = test_index_creation()
    pprint.pprint(query(index=ix, query_str="movie"))
    pprint.pprint(query(index=ix, query_str="color"))
    pprint.pprint(query(index=ix, query_str="mv"))
    pprint.pprint(query(index=ix, query_str="threshold"))
