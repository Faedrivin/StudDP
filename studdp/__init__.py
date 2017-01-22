import json
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

if not os.path.exists(CONFIG_FILE):
    os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(DEFAULT_CONFIG, f, sort_keys=True, indent=4 * ' ')
with open(CONFIG_FILE, 'r') as rfile:
    CONFIG = json.load(rfile)
