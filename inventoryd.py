#!/usr/bin/python -tt
# -*- coding: utf-8 -*-
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4

import inventoryd
import os
import sys
import iniparse
import signal
import json

daemon = None

def main():
    global daemon
    inventoryd.localData.cli = inventoryd.getcliargs()
    inventoryd.localData.cfg = inventoryd.getconfig(inventoryd.localData.cli.configpath)
    daemon = inventoryd.daemon()
    daemon.start()

    signal.signal(signal.SIGINT, signal_handler)
    signal.pause()
    sys.exit(0)
    db = inventoryd.db(inventoryd.localData.cfg["db"])

def signal_handler(signal, frame):
    global daemon
    daemon.stop()
    sys.exit(0)



if __name__ == '__main__':
    main()
