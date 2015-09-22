#!/usr/bin/python -tt
# -*- coding: utf-8 -*-
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import inventoryd
import os
import sys
import iniparse
import signal
import json
from threading import Thread

daemon = None

def main():
    global daemon
    inventoryd.localData.cli = inventoryd.getcliargs()
    inventoryd.localData.cfg = inventoryd.getconfig(inventoryd.localData.cli.configpath)
    
    if inventoryd.localData.cli.daemonize is True:

        try:
            pid = os.fork()
        except OSError, e:
            raise Exception, "%s [%d]" % (e.strerror, e.errno)
        
        if pid == 0:
            os.setsid()
            try:
                pid = os.fork()
            except OSError, e:
                raise Exception, "%s [%d]" % (e.strerror, e.errno)
            
            if pid == 0:
                os.chdir("/")
                os.umask(0)
                daemon = inventoryd.daemon()
                daemon.start()

                signal.signal(signal.SIGINT, signal_handler)
                signal.pause()
                sys.exit(0)
            else:
                os._exit(0)
        else:
            os._exit(0)
    else:
        daemon = inventoryd.daemon()
        daemon.start()

        signal.signal(signal.SIGINT, signal_handler)
        signal.pause()
        sys.exit(0)

    
def signal_handler(signal, frame):
    global daemon
    daemon.stop()
    sys.exit(0)



if __name__ == '__main__':
    main()
