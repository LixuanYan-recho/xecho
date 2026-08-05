import os
import sys


def get_environment_value(name):
    value = os.environ.get(name)
    if value:
        return value
    if sys.platform != "win32":
        return None
    return _read_windows_environment(name)


def _read_windows_environment(name):
    import winreg

    locations = (
        (winreg.HKEY_CURRENT_USER, r"Environment"),
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
        ),
    )
    for hive, path in locations:
        try:
            with winreg.OpenKey(hive, path) as key:
                value, _ = winreg.QueryValueEx(key, name)
        except (FileNotFoundError, OSError):
            continue
        if value:
            return str(value)
    return None

