from __future__ import print_function

__author__ = "Viktor Kerkez <alefnula@gmail.com>"
__date__ = "18 September 2012"
__copyright__ = "Copyright (c) 2013 Viktor Kerkez"

import io
import os
import sys
import time
import atexit
from signal import SIGTERM

from tea.system import platform

if platform.is_a(platform.POSIX):

    class Daemon(object):
        """Generic daemon class.

        Usage: subclass the Daemon class and override the run() method
        """

        def __init__(
            self,
            pidfile,
            stdin="/dev/null",
            stdout="/dev/null",
            stderr="/dev/null",
        ):
            self.stdin = stdin
            self.stdout = stdout
            self.stderr = stderr
            self.pidfile = pidfile

        def daemonize(self):
            """Do the UNIX double-fork magic.

            See Stevens' "Advanced Programming in the UNIX Environment" for
            details (ISBN 0201563177)
            http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
            """
            try:
                pid = os.fork()
                if pid > 0:
                    # exit first parent
                    sys.exit(0)
            except OSError as e:
                sys.stderr.write(
                    "fork #1 failed: %d (%s)\n" % (e.errno, e.strerror)
                )
                sys.exit(1)

            # decouple from parent environment
            os.chdir("/")
            os.setsid()
            os.umask(0)

            # do second fork
            try:
                pid = os.fork()
                if pid > 0:
                    # exit from second parent
                    sys.exit(0)
            except OSError as e:
                sys.stderr.write(
                    "fork #2 failed: %d (%s)\n" % (e.errno, e.strerror)
                )
                sys.exit(1)

            # redirect standard file descriptors
            sys.stdout.flush()
            sys.stderr.flush()
            si = io.open(self.stdin, "rb")
            so = io.open(self.stdout, "ab+")
            se = io.open(self.stderr, "ab+")
            os.dup2(si.fileno(), sys.stdin.fileno())
            os.dup2(so.fileno(), sys.stdout.fileno())
            os.dup2(se.fileno(), sys.stderr.fileno())

            # write pidfile
            atexit.register(self.delpid)
            pid = str(os.getpid())
            io.open(self.pidfile, "w+").write("%s\n" % pid)

        def delpid(self):
            os.remove(self.pidfile)

        def start(self, *args):
            """Start the daemon."""
            # Check for a pidfile to see if the daemon already runs
            try:
                pf = io.open(self.pidfile, "r")
                pid = int(pf.read().strip())
                pf.close()
            except IOError:
                pid = None

            if pid:
                message = "pidfile %s already exist. Daemon already running?\n"
                sys.stderr.write(message % self.pidfile)
                sys.exit(1)

            # Start the daemon
            self.daemonize()
            self.run(*args)

        def stop(self):
            """Stop the daemon."""
            # Get the pid from the pidfile
            try:
                pf = io.open(self.pidfile, "r")
                pid = int(pf.read().strip())
                pf.close()
            except IOError:
                pid = None

            if not pid:
                message = "pidfile %s does not exist. Daemon not running?\n"
                sys.stderr.write(message % self.pidfile)
                return  # not an error in a restart

            # Try killing the daemon process
            try:
                while 1:
                    os.kill(pid, SIGTERM)
                    time.sleep(0.1)
            except OSError as err:
                err = str(err)
                if err.find("No such process") > 0:
                    if os.path.exists(self.pidfile):
                        os.remove(self.pidfile)
                else:
                    print(str(err))
                    sys.exit(1)

        def restart(self, *args):
            """Restart the daemon."""
            self.stop()
            self.start(*args)

        def run(self, *args):
            """You should override this method when you subclass Daemon.

            It will be called after the process has been daemonized by start()
            or restart().
            """
            pass
