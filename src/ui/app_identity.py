"""Stable Windows identity, configured before QApplication creates native windows."""
import logging
import sys

APP_ID = "gggg-unit.TusKlavye.Desktop"


def configure_app_identity():
    if sys.platform != "win32":
        return
    try:
        import ctypes
        setter = ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID
        setter.argtypes = [ctypes.c_wchar_p]
        setter.restype = ctypes.c_long
        result = setter(APP_ID)
        if result != 0:
            logging.getLogger(__name__).warning("Windows app identity failed: %s", result)
    except (AttributeError, OSError) as error:
        logging.getLogger(__name__).warning("Windows app identity unavailable: %s", error)
