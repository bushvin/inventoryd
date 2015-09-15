# Copyright (c) 2015 William Leemans <willie@elaba.net>
#
# This file is part of inventoryd
#
# inventoryd is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# inventoryd is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with inventoryd; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA.

import inventoryd 
import os, sys
import iniparse

def getconfig(configpath):
    validpath = False;
    if configpath is None:
        loclist = [ "/etc/inventory/inventoryd.cfg", "~/.inventory.cfg", "~/.inventory" ]
        for loc in loclist:
            if os.path.isfile(os.path.expanduser(loc)) is True:
                configpath = os.path.expanduser(loc)
                validpath = True
                break
    else:
        if os.path.isfile(os.path.expanduser(configpath)) is True:
            validpath = True

    if validpath is False:
        inventoryd.logmessage(severity="crit", message="Config file not found. Aborting.")
        sys.exit(1)
    
    with open(configpath) as inifile:
        ini = iniparse.INIConfig(inifile)

    newini = { 'inventoryd': {
                    'connector_path': None,
                    'log_facility': 'local1',
                    'log_level': 'debug' },
               'housekeeper': {
                    'schedule':'@hourly',
                    'history': 24 },
               'rest_server': {
                    'listen': '0.0.0.0',
                    'http_port': 8080,
                    'https_port': 8443,
                    'ssl_certificate': None,
                    'ssl_keyfile': None },
               'inventory': {
                    'create_all': True,
                    'create_localhost': True,
                    'localhost_connection': 'local' }
             }
    for section in list(ini):
        for option in list(ini[section]):
            try:
                newini[section]
            except:
                newini[section] = {}
            newini[section][option] = ini[section][option]

    newini["housekeeper"]["history"] = int(newini["housekeeper"]["history"])
    newini["rest_server"]["http_port"] = int(newini["rest_server"]["http_port"])
    newini["rest_server"]["https_port"] = int(newini["rest_server"]["https_port"])
    newini["inventory"]["create_all"] = bool(newini["inventory"]["create_all"])
    newini["inventory"]["create_localhost"] = bool(newini["inventory"]["create_localhost"])
    return newini
    
