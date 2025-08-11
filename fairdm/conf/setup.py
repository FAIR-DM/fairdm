import inspect
import logging
import os
from pathlib import Path
import importlib.util
from importlib import import_module
import os
import environ
from split_settings.tools import include


logger = logging.getLogger(__name__)

addon_urls = []


def get_module_path(module_name: str) -> str:
    """
    Given a module name like 'myapp.utils.helpers', return the file system path
    to the .py file.

    Raises:
        ModuleNotFoundError: if the module can't be found.
        ValueError: if the module is a package (i.e. __init__.py).
    """
    spec = importlib.util.find_spec(module_name)
    if spec is None or spec.origin is None:
        raise ModuleNotFoundError(f"Module '{module_name}' not found")

    if spec.submodule_search_locations:
        raise ValueError(f"'{module_name}' is a package, not a module")

    return os.path.abspath(spec.origin)


def import_addons_settings(addons):
    """Get a list of settings modules for the given addons. The full path of each module is returned allowing
    use of the split_settings.include function."""
    fdm_setup_modules = []
    for addon in addons:
        module = import_module(addon)
        addon_fdm_setup_module = getattr(module, "__fdm_setup_module__", None)
        if addon_fdm_setup_module is None:
            logger.warning(f"Addon '{addon}' does not define __fdm_setup_module__; skipping.")
            continue
        try:
            fdm_setup_modules.append(get_module_path(addon_fdm_setup_module))
        except Exception as e:
            logger.warning(f"Could not import setup module '{addon_fdm_setup_module}' for addon '{addon}': {e}")
    return fdm_setup_modules


def setup(apps=[], addons=[], base_dir=None):
    """Adds all the default variables defined in fairdm.conf.settings to the global namespace.

    Args:
        development (bool): Whether or not to load development settings. Defaults to False.
    """

    DJANGO_ENV = os.environ.get("DJANGO_ENV")

    globals = inspect.stack()[1][0].f_globals
    if not base_dir:
        base_dir = Path(globals["__file__"]).resolve(strict=True).parent.parent

    globals.update(
        {
            "FAIRDM_APPS": apps,
            "DJANGO_ENV": DJANGO_ENV,
            "BASE_DIR": base_dir,
            "__file__": os.path.realpath(__file__),
        }
    )
    # environ.Env.read_env(".env")

    if DJANGO_ENV == "development":
        # print("Loading development settings")
        # read any override config from the .env file
        environ.Env.read_env("stack.development.env")
        environ.Env.read_env("stack.env")
        logger.warning("Using development settings")
        # env("DJANGO_INSECURE", default=True)
        # os.environ.setdefault("DJANGO_INSECURE", "True")
        include(
            "environment.py",
            "settings/general.py",
            "settings/*.py",
            "dev_overrides.py",
            scope=globals,
        )
    else:
        # read any override config from the stack.env file (if it exists)
        environ.Env.read_env("stack.env")
        logger.warning("Using production settings")
        include(
            "environment.py",
            "settings/general.py",
            "settings/*.py",
            scope=globals,
        )

    # find any required settings modules specified by addons and import them
    include(*import_addons_settings(addons), scope=globals)

    # find any urls.py files in the addons and include them, these will be automatically added to the urlpatterns
    # in fairdm.conf.urls
    for addon in addons:
        try:
            spec = importlib.util.find_spec(f"{addon}.urls")
            if spec is not None and spec.origin is not None:
                addon_urls.append(f"{addon}.urls")
        except Exception as e:
            pass
            # logger.warning(f"Could not check for urls.py in addon '{addon}': {e}")
