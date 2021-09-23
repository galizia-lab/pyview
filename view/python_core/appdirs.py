import appdirs
# https://github.com/ActiveState/appdirs


def get_app_log_dir():
    """
    Get the the log directory for VIEW
    :return: str, directory path on file system
    """

    name, org, domain = get_app_name_organization_domain()
    return appdirs.user_log_dir(appname=name,
                                appauthor=org)


def get_app_usr_data_dir():
    """
    Get the the log directory for VIEW
    :return: str, directory path on file system
    """

    name, org, domain = get_app_name_organization_domain()
    return appdirs.user_data_dir(appname=name,
                                 appauthor=org)


def get_app_name_organization_domain():
    """
    Returns name, organization and domain to be used with VIEW
    :return: tuple of strings
    """

    return "VIEW", "UKN_Neuro", "neuro.uni-konstanz.de"