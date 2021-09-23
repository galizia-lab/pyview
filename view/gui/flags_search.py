from whoosh import index as windex
from whoosh import fields as wfields
from whoosh import qparser as wqparser
import view
from ..python_core.appdirs import get_app_usr_data_dir
import pathlib as pl
from ..python_core.flags import FlagsManager


def get_index_dir():
    """
    Return the path of the directory used for storing indexing files
    :return: pathlib.Path object
    """

    return pl.Path(get_app_usr_data_dir()) / "flags_text_index"


def get_indexname():
    """
    Returns the index name corresponding to the current version of VIEW
    """

    return view.__version__.replace("+", "_")


def check_if_index_is_correct(index_dir: pl.Path):
    """
    Open the index if possible, check whether the index is of the current version of VIEW. If true return the
    index, else delete the index directory and return None
    :param index_dir: pathlib.Path object, pointing to a directory on file system
    :return: whoosh.index.FileIndex or None
    """

    if not index_dir.is_dir():
        return False
    elif windex.exists_in(str(index_dir), indexname=get_indexname()):
        return True
    else:
        return False


def get_schema():
    """
    creates and returns the schema used for indexing flag data
    """
    return wfields.Schema(flag_name=wfields.KEYWORD(stored=True), flag_subgroup=wfields.STORED,
                          flag_description=wfields.TEXT(stored=True))


def create_new_index(index_dir, flags):
    """
    create a new index and return it, exluding deprecated flags
    """
    index_dir.mkdir(parents=True, exist_ok=True)
    ix = windex.create_in(dirname=str(index_dir), schema=get_schema(), indexname=get_indexname())
    index_writer = ix.writer()
    for flag_subgroup in flags.get_subgroups():
        subgroup_definition = flags.get_subgroup_definition(flag_subgroup)
        for flag_index, (flag_name, flag_default, flag_description, selectable_options, flag_value_type) \
                in subgroup_definition.iterrows():
            index_writer.add_document(flag_name=flag_name, flag_description=flag_description,
                                      flag_subgroup=flag_subgroup)
    index_writer.commit()

    return ix


def get_flags_index(flags: FlagsManager):
    """
    Checks if an index for this version of VIEW exists. If it does returns. Else, creates one and returns it.
    :param flags: flags object
    :returns: index object
    """

    index_dir = get_index_dir()

    if check_if_index_is_correct(index_dir):
        return windex.open_dir(str(index_dir), indexname=get_indexname())
    else:
        return create_new_index(index_dir, flags)


def query(index, query_str: str, max_results: int = 5):

    query_str = f"*{query_str}*"

    with index.searcher() as searcher:

        name_qp = wqparser.QueryParser("flag_name", schema=index.schema)
        description_qp = wqparser.QueryParser("flag_description", schema=index.schema)

        name_query = name_qp.parse(query_str)
        description_query = description_qp.parse(query_str)

        name_results = searcher.search(name_query, limit=20)
        desc_results = searcher.search(description_query, limit=20)

        highlights = []

        for hit in name_results:
            if len(highlights) < max_results:
                highlight = {}
                highlight["flag_name"] = hit.highlights("flag_name")
                highlight["flag_subgroup"] = hit["flag_subgroup"]
                highlight["flag_description"] = f"{hit['flag_description'][:100]}..."
                highlight["which"] = "flag_name"
                highlights.append(highlight)

        for hit in desc_results:
            if len(highlights) < max_results:
                highlight = {}
                highlight["flag_description"] = f"...{hit.highlights('flag_description')}..."
                highlight["flag_subgroup"] = hit["flag_subgroup"]
                highlight["flag_name"] = hit["flag_name"]
                highlight["which"] = "flag_desc"
                highlights.append(highlight)

    return highlights










