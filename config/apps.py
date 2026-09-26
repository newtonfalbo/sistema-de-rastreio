from django.contrib.admin.apps import AdminConfig


class RastreioAdminConfig(AdminConfig):
    default_site = 'config.admin.SuperuserAdminSite'
