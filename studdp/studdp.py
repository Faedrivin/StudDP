from .config import configuration as c
from .model import APIClient
import sys
from os.path import expanduser, join
import os
import optparse
import daemon
from daemon.pidfile import PIDLockFile
import time
import logging
from . import LOG_PATH

log = logging.getLogger(__name__)

PID_FILE = expanduser(join('~', '.studdp', 'studdp.pid'))


def _parse_args():
    parser = optparse.OptionParser()
    parser.add_option("-c", "--config",
                      action="store_true", dest="select", default=False,
                      help="change course selection")
    parser.add_option("-s", "--stop",
                      action="store_true", dest="stop", default=False,
                      help="stop the daemon process")
    parser.add_option("-d", "--daemonize",
                      action="store_true", dest="daemonize", default=False,
                      help="start as daemon. Use stopDP to end thread.")
    parser.add_option("-f", "--force",
                      action="store_true", dest="update_courses", default=False,
                      help="overwrite local changes")
    return parser.parse_args()


class _MainLoop:

    def __init__(self, daemonize, overwrite):
        self.daemonize = daemonize
        self.overwrite = overwrite

    def __call__(self):
        while True:
            courses = APIClient.get_courses()

            for course in courses:
                if not c.is_selected(course):
                    log.debug("Skipping files for %s" % course)
                    continue
                log.info("Checking files for %s..." % course)
                for document in course.deep_documents:
                    document.download(self.overwrite)

            c.update_time()
            log.info("Finished checking.")
            if not self.daemonize:
                return
            time.sleep(c.config["interval"])


def main():

    (options, args) = _parse_args()

    if options.select:
        courses = APIClient.get_courses()
        c.selection_dialog(courses)
        sys.exit(0)

    if options.stop:
        os.system("kill -2 `cat ~/.studdp/studdp.pid`")
        sys.exit(0)

    task = _MainLoop(options.daemonize, options.update_courses)

    if options.daemonize:
        log.info("daemonizing...")
        with daemon.DaemonContext(pidfile=PIDLockFile(PID_FILE)):
            # we have to create a new logger in the daemon context
            handler = logging.FileHandler(LOG_PATH)
            handler.setFormatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
            log.addHandler(handler)
            task()
    else:
        task()


if __name__ == "__main__":
    main()