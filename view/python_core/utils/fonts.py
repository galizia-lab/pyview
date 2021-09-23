import pathlib as pl

from matplotlib import font_manager
from view.python_core.get_internal_files import get_internal_fonts_dir
from PIL import ImageFont


def resolve_font_file(mv_fontName):
    """
    Find a font file on the file system, if not found, use internal default
    Hierarchy for file look up: (1) system ttf font with name mv_fontName, (2) system otf font with name mv_fontName,
    (3) internal ttf font with name mv_fontName (4) internal otf font with name mv_fontName, fallback internal font
    :param str mv_fontName: name of the font, will look for <mv_fontname>.ttf or <mv_fontname>.otf
    :rtype: str
    :returns: absolute filename of the font file
    """

    font_file_lookup_hierarchy = [find_font_file_in_OS(font_name=mv_fontName, ext=".ttf"),
                                  find_font_file_in_OS(font_name=mv_fontName, ext=".otf"),
                                  find_font_file_in_dir(font_name=mv_fontName, where=get_internal_fonts_dir(),
                                                        ext=".ttf"),
                                  find_font_file_in_dir(font_name=mv_fontName, where=get_internal_fonts_dir(),
                                                        ext=".otf"),
                                  find_font_file_in_dir(font_name="PixelOperator8", where=get_internal_fonts_dir(),
                                                        ext=".ttf")]

    existences = [x is not None for x in font_file_lookup_hierarchy]
    font2use = font_file_lookup_hierarchy[existences.index(True)]

    return font2use


def get_maximum_font_size_by_width(font_name, text, maximum_width):

    font = ImageFont.truetype(font=font_name, size=10)

    w, h = font.getsize(text)

    return int(10 * maximum_width / w)


def resolve_font_size(suggested_font_size, maximum_width, text, font_name):
    max_font_size = get_maximum_font_size_by_width(font_name=font_name, text=text,
                                                   maximum_width=maximum_width)
    max_font_size_with_margin = int(0.95 * max_font_size)
    return max(min(max_font_size_with_margin, suggested_font_size), 8)


def find_font_file_in_dir(font_name, where=None, ext=".ttf"):

    font_files = font_manager.findSystemFonts(fontpaths=where)
    matches = [pl.Path(f).name.lower() == f"{font_name}{ext}".lower() for f in font_files]

    if any(matches):
        return font_files[matches.index(True)]
    else:
        return None


def find_font_file_in_OS(font_name, ext=".ttf"):

    return find_font_file_in_dir(font_name, ext=ext)