#!/usr/bin/python3

"""
StudDP downloads files from Stud.IP.
"""

import json
import logging
import os
import shutil
import signal
import time
import sys
import requests
import re
import optparse
from distutils.util import strtobool
import keyring
import getpass
import atexit
from .picker import Picker
from .APIWrapper import APIWrapper
from . import CONFIG
from . import CONFIG_FILE

LOG = logging.getLogger(__name__)
LOG_PATH = os.path.expanduser(os.path.join('~', '.studdp'))
PID_FILE = os.path.expanduser(os.path.join('~', '.studdp', 'studdp.pid'))
WIN_INVALID_CHARACTERS = [":", "<", ">", "|", "\?", "\*"]


class StudDP(object):
    """
    The main program loops until interrupted.
    Every time files were changed after the last check, they are downloaded.
    Files are also downloaded if they do not exist locally.
    """

    def __init__(self,
                 config,
                 api_helper,
                 daemonize=False,
                 on_windows=False,
                 update=False):
        """
        Initializes the API and the update frequencies.
        """
        self.config = config
        self.interval = self.config['interval']
        self.api = api_helper
        self.daemonize = daemonize
        self.on_windows = on_windows
        self.update = update

    def _needs_download(self, document):
        """
        Checks if a download of the document is needed.
        """
        return ((int(document['chdate']) > self.config['last_check']) and
                self.update) or not \
            os.path.exists(os.path.join(document['path'],
                                        document['filename']))

    def __call__(self):
        """
        Starts the main loop and checks
        periodically for document changes and downloads.
        """
        while True:
            try:
                courses = self.api.get_courses()
            except Exception:
                LOG.exception("Getting courselist failed. Stacktrace:")

            if not self.config['courses_selected']:
                LOG.info("Updating course selection")
                titles = map(lambda x: x["title"], courses)
                selection = Picker(
                    title="Select courses to download",
                    options=titles,
                    checked=self.config['selected_courses']).getSelected()
                self.config["courses_selected"] = True
                if not selection:
                    return
                self.config['selected_courses'] = selection

            LOG.info('Checking courses.')
            for course in courses:
                title = course['title']
                LOG.debug('Course: %s', title)

                if title in self.config['selected_courses']:
                    LOG.info('Checking files for %s', title)
                    try:
                        documents = self.api.get_documents(course)
                    except Exception:
                        LOG.exception("Getting course %s failed. Stacktrace:" \
                                      % course["title"])
                        continue
                    for document in documents:
                        if self.on_windows:  # Salt Path
                            for char in WIN_INVALID_CHARACTERS:
                                document["path"] = re.sub(
                                    char, "", document["path"])
                                document["filename"] = re.sub(
                                    char, "", document["filename"])
                        if self._needs_download(document):
                            path = os.path.join(
                                document['path'], document['filename'])
                            LOG.info('Downloading %s...', path)
                            try:
                                self.api.download_document(document, path)
                                LOG.debug('Saved %s', path)
                            except Exception:
                                LOG.exception("Downloading to %s failed. Stacktrace:" % path)
                else:
                    LOG.debug('Skipping files for %s', title)
            self.config['last_check'] = time.time()
            LOG.info('Done checking.')
            if not self.daemonize:
                return
            time.sleep(self.interval)


def _setup_logging(log_to_stdout=False):
    """
    Sets up the logging handlers.
    """
    os.makedirs(LOG_PATH, exist_ok=True)
    file_handler_info = logging.FileHandler(os.path.join(LOG_PATH, 'info.log'))
    file_handler_info.setLevel(logging.DEBUG)
    file_handler_info.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    LOG.addHandler(file_handler_info)
    if log_to_stdout:
        out = logging.StreamHandler(sys.stdout)
        out.setLevel(logging.INFO)
        out.setFormatter(logging.Formatter(
            '%(name)s - %(levelname)s - %(message)s'))
        LOG.addHandler(out)
    err = logging.StreamHandler(sys.stderr)
    err.setLevel(logging.ERROR)
    err.setFormatter(logging.Formatter(
        '%(name)s - %(levelname)s - %(message)s'))
    LOG.addHandler(err)
    LOG.setLevel(logging.DEBUG)
    LOG.info('Logging initialized.')


def _get_password(username, force_update=False):
    if username == "":
        print("No username provided. "
              "Please configure ~/.config/studdp/config.json first")
        exit()
    LOG.info("Querying for password")
    password = keyring.get_password("StudDP", username)
    if not password or force_update:
        password = getpass.getpass(
            "Please enter password for user %s: " % username)
        LOG.info("Adding new password to keyring")
        keyring.set_password("StudDP", username, password)
    return password


def _exit_func():
    """
    Ensures clean exit by writing the current configuration file and
    deleting the pid file.
    """
    LOG.info('Invoking exit.')
    with open(CONFIG_FILE, 'w') as wfile:
        LOG.info('Writing config.')
        json.dump(CONFIG, wfile, sort_keys=True, indent=4 * ' ')
    os.unlink(PID_FILE)
    LOG.info('Exiting.')


def _parse_args():
    parser = optparse.OptionParser()
    parser.add_option("-c", "--config",
                      action="store_true", dest="regenerate", default=False,
                      help="change course selection")
    parser.add_option("-v", "--verbose",
                      action="store_true", dest="log_to_stdout", default=False,
                      help="print log to stdout")
    parser.add_option("-d", "--daemonize",
                      action="store_true", dest="daemonize", default=False,
                      help="start as daemon. Use stopDP to end thread.")
    parser.add_option("-w", "--windows",
                      action="store_true", dest="on_windows", default=False,
                      help="remove characters that are forbidden in windows paths")
    parser.add_option("-u", "--update",
                      action="store_true", dest="update_courses", default=False,
                      help="update files when they are updated on StudIP")
    parser.add_option("-p", "--password",
                      action="store_true", dest="update_password", default=False,
                      help="force password update")
    return parser.parse_args()


def main():
    (options, args) = _parse_args()
    _setup_logging(options.log_to_stdout)

    username = CONFIG["username"]
    password = _get_password(username, options.update_password)

    os.makedirs(os.path.dirname(PID_FILE), exist_ok=True)
    with open(PID_FILE, 'w') as pid_file:
        pid_file.write(str(os.getpid()))

    atexit.register(_exit_func)

    if options.regenerate:
        CONFIG["courses_selected"] = False


    api_helper = APIWrapper((username, password), CONFIG["base_address"],
                            CONFIG["local_path"])

    StudDP(CONFIG, api_helper, options.daemonize, options.on_windows,
           options.update_courses)()

if __name__ == "__main__":
    main()
