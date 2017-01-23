import os

DEFAULT_CONFIG = {
    "username": "",
    "base_address": "https://studip.uos.de/plugins.php/restipplugin",
    "local_path": "~/studip",
    "interval": 1200,
    "last_check": -1,
    "courses_selected": False,
    "selected_courses": []
}


CONFIG_FILE = os.path.expanduser(
    os.path.join("~", ".config", "studdp", 'config.json'))


