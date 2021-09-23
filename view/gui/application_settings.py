from PyQt5.QtCore import QCoreApplication, QSettings
from ..python_core.appdirs import get_app_name_organization_domain


def initialize_app_settings():
    """
    Initialize application Name, Organization Name and Domain
    """
    name, org, domain = get_app_name_organization_domain()
    QCoreApplication.setApplicationName(name)
    QCoreApplication.setOrganizationName(org)
    QCoreApplication.setOrganizationDomain(domain)


def get_view_qsettings_manager():
    """
    :return: a QSettings object which can be used to access view configuration values
    """
    name, org, domain = get_app_name_organization_domain()
    return QSettings(org, name)


