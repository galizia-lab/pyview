import pkg_resources


def get_icon_path(icon_name_with_extension):
    return pkg_resources.resource_filename('view', f"graphics/icons/{icon_name_with_extension}")


