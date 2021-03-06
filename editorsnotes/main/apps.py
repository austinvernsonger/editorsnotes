from django.apps import AppConfig
from django.db.models.signals import post_migrate


def update_permissions_after_migration(**kwargs):
    """
    Create permissions for apps synced with South even when do not change.

    Django creates new custom permissions (defined in a model's Meta class
    when the app of that model gives a post_syncdb signal. South only fires
    that signal, however, when new migrations are applied to that app. So if
    any new permissions are added without any models changing (or, I suppose,
    a dummy migration is added), those new permission will not be created.

    Hooking to the post_migrate signal ensures that such new permissions will
    be created, along with the project specific permissions created from
    management.update_project_permissions.

    South bug:
        http://south.aeracode.org/ticket/211
    Adapted solution:
        http://devwithpassion.com/felipe/south-django-permissions/
    """

    from .management import update_project_permissions
    update_project_permissions()


class MainAppConfig(AppConfig):
    name = 'editorsnotes.main'
    verbose_name = 'Editors\' Notes main'

    def ready(self):
        post_migrate.connect(update_permissions_after_migration)
