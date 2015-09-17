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
import inventoryd.connector_uri as connector_uri
from threading import Timer
import os
import sys
import datetime
from threading import Thread
import json
import re

class daemon:
    _cfg = None
    _cli = None
    _https_restserver = None
    _http_restserver = None
    _scheduleTimer = None
    _housekeeper_lock = False
    _connector_lock = False
    
    def __init__(self):
        self._cfg = inventoryd.localData.cfg
        self._cli = inventoryd.localData.cli
        inventoryd.logmessage(severity="debug", message="Checking for connector path")
        if self._cfg["inventoryd"]["connector_path"] is not None and os.path.isdir(self._cfg["inventoryd"]["connector_path"]) is True:
            inventoryd.logmessage(severity="info", message="Adding %s to path" % self._cfg["inventoryd"]["connector_path"])
            sys.path.append(self._cfg["inventoryd"]["connector_path"])
        elif self._cfg["inventoryd"]["connector_path"] is not None:
            inventoryd.logmessage(severity="warn", message="%s could not be found. Does it exist?" % self._cfg["inventoryd"]["connector_path"])

    def start(self):
        self._createPID()
        self._startRESTserver()
        self._startScheduler()

    def stop(self, force = False):
        self._stopRESTserver()
        self._stopScheduler()
        self._destroyPID()
    
    def _createPID(self):
        pid = str(os.getpid())
        
        if os.path.isfile(self._cli.pidfilepath) is True:
            inventoryd.logmessage(severity="crit", message="A pidfile (%s) for inventoryd has been found. Aborting startup." % self._cli.pidfilepath)
            sys.exit(1)
        else:
            inventoryd.logmessage(severity="debug", message="No pidfile found. Starting inventoryd.")
            try:
                file(self._cli.pidfilepath, 'w').write(pid)
            except IOError as e:
                inventoryd.logmessage(severity="crit", message="Could not create pidfile.")
                inventoryd.logmessage(severity="crit", message="Error ({0}): {1}".format(e.errno, e.strerror))
                sys.exit(1)
            except:
                inventoryd.logmessage(severity="crit", message="Could not create pidfile.")
                sys.exit(1)
                
        
    def _destroyPID(self):
        inventoryd.logmessage(severity="debug", message="Removing pidfile.")
        try:
            os.unlink(self._cli.pidfilepath)
        except OSError as e:
                inventoryd.logmessage(severity="crit", message="Could not remove pidfile.")
                inventoryd.logmessage(severity="crit", message="Error ({0}): {1}".format(e.errno, e.strerror))
                sys.exit(1)
        except:
                inventoryd.logmessage(severity="crit", message="Could not remove pidfile.")
                sys.exit(1)
    
    def _startScheduler(self):
        inventoryd.logmessage(severity="info", message="Starting the task scheduler")
        inventoryd.logmessage(severity="info", message="Housekeeping schedule: %s" % self._cfg["housekeeper"]["schedule"])
        db = inventoryd.db(self._cfg["db"])
        for el in db.getConnectors():
            inventoryd.logmessage(severity="info", message="Sync connector '%s' schedule: %s" % (el["name"], el["schedule"]))
        db.disconnect()
        interval = 61 - datetime.datetime.now().second
        self._scheduleTimer = Timer(interval, self._runScheduler)
        self._scheduleTimer.start()
    
    def _stopScheduler(self):
        if self._scheduleTimer is not None:
            inventoryd.logmessage(severity="info", message="Stopping the task scheduler")
            self._scheduleTimer.cancel()
        
    def _runScheduler(self):
        inventoryd.logmessage(severity="info", message="Starting scheduled tasks")
        interval = 61 - datetime.datetime.now().second
        inventoryd.logmessage(severity="info", message="Next scheduled tasks run in %ds" %interval)
        self._scheduleTimer = Timer(interval, self._runScheduler)
        self._scheduleTimer.start()
        cron = inventoryd.cronpare()
        db = inventoryd.db(self._cfg["db"])
        if self._connector_lock is False:
            self._connector_lock = True
            for el in db.getConnectors():
                inventoryd.logmessage(severity="info", message="Checking schedule for %s:%s" % (el["name"], el["schedule"]))
                if cron.compare(el["schedule"]) is True:
                    inventoryd.logmessage(severity="info", message="Starting sync run for %s" % el["name"])
                    self._sync_connector(el["id"])
                    inventoryd.logmessage(severity="info", message="Ending sync run for %s" % el["name"])
            self._connector_lock = False

        if self._connector_lock is False:
            if cron.compare(self._cfg["housekeeper"]["schedule"]) is True:
                if self._housekeeper_lock is False:
                    self._housekeeper_lock = True
                    inventoryd.logmessage(severity="info", message="Starting Housekeeping run")
                    if self._cfg["housekeeper"]["history"] > 0:
                        db.deleteHistory(self._cfg["housekeeper"]["history"])
                    if self._cfg["housekeeper"]["inventory_history"] > 0:
                        cachefiles = list()
                        for el in os.listdir(self._cli.cachefilepath):
                            if re.match("^[0-9]+.json", el) is not None:
                                cachefiles.append(el)
                        cachefiles.sort()
                        cachefiles = cachefiles[:0-self._cfg["housekeeper"]["inventory_history"]]
                        inventoryd.logmessage(severity="info", message="Removing %d old cache files" % len(cachefiles))
                        for el in cachefiles:
                            inventoryd.logmessage(severity="info", message="Removing old cache file %s" % el)
                            try:
                                os.unlink("%s/%s" % (self._cli.cachefilepath, el))
                            except OSError as e:
                                inventoryd.logmessage(severity="error", message="An error ocurred removing %s: %s" % (el, e))
                            except:
                                inventoryd.logmessage(severity="error", message="An error ocurred removing %s" % el)
                    inventoryd.logmessage(severity="info", message="Ending Housekeeping run")
                    self._housekeeper_lock = False
                else:
                    inventoryd.logmessage(severity="info", message="Skipping Housekeeping run. Still busy.")
        else:
            inventoryd.logmessage(severity="info", message="Skipping Housekeeping run. Connector Sync is still busy.")
            
        db.disconnect()
        inventoryd.logmessage(severity="info", message="Endinging scheduled tasks")
        
    
    def _sync_connector(self, connector_id):
        db = inventoryd.db(self._cfg["db"])
        connector = db.getConnector(connector_id)
        if connector is None:
            return False
        hid = db.startHistoryItem(connector["id"])
        
        try:
            exec "connector_%s" % connector["connector"]
        except:
            libpath = self._cfg["inventoryd"]["connector_path"]
            inventoryd.logmessage(severity="debug", message="Connector %s hasn't been imported yet. Attempting." % connector["connector"])
            execute_connector = False
            
            if libpath is not None and os.path.isdir(self._cfg["inventoryd"]["connector_path"]):
                inventoryd.logmessage(severity="debug", message="inventoryd.connector_path is set and connector library exists!")
                try:
                    exec "import connector_%s" % connector["connector"]
                except:
                    inventoryd.logmessage(severity="crit", message="Could not import the connector %s" % connector["connector"])
                else:
                    exec "import connector_%s" % connector["connector"]
                    execute_connector = True
                    
            elif libpath is not None:
                inventoryd.logmessage(severity="err", message="inventoryd.connector_path is set but connector library doesn't exist!")
            elif libpath is None:
                inventoryd.logmessage(severity="debug", message="inventoryd.connector_path is not set")
        else:
            execute_connector = True
            
        if execute_connector is True:
            inventoryd.logmessage(severity="info", message="Syncing %s" % connector["name"])
            exec "cc = connector_%s(connector['parameters'])" % connector["connector"]
            if connector["type"] == "hosts":
                facts = cc.getHosts()
                if cc.rc == 0:
                    inventoryd.logmessage(severity="info", message="%s - synchronizing %d hostvar facts for %d hosts" % (connector["name"], len(facts), int(cc.getHostCount())))
                    db.commitHostsCache(hid,facts)
                    inventoryd.logmessage(severity="debug", message="%s - %d hostvar facts synchronized" % (connector["name"], len(facts)))
                else:
                    inventoryd.logmessage(severity="error", message="%s - An error occurred synchronizing hostvars. RC:%d" % (connector["name"],cc.rc))
                    inventoryd.logmessage(severity="error", message="%s - %s" % (connector["name"],cc.message))
            else:
                facts, hosts, children = cc.getGroups()
                if cc.rc == 0:
                    inventoryd.logmessage(severity="info", message="%s - synchronizing %d groupvar facts" % (connector["name"], len(facts)))
                    inventoryd.logmessage(severity="info", message="%s - synchronizing %d group host memberships" % (connector["name"], len(hosts)))
                    inventoryd.logmessage(severity="info", message="%s - synchronizing %d group group memberships" % (connector["name"], len(children)))
                    db.commitGroupsCache(hid,facts, hosts, children)
                    inventoryd.logmessage(severity="debug", message="%s - %d groupvar facts synchronized" % (connector["name"], len(facts)))
                    inventoryd.logmessage(severity="debug", message="%s - %d group host memberships synchronized" % (connector["name"], len(hosts)))
                    inventoryd.logmessage(severity="debug", message="%s - %d group group memberships synchronized" % (connector["name"], len(children)))
                else:
                    inventoryd.logmessage(severity="error", message="%s - An error occurred synchronizing groups. RC:%d" % (connector["name"], cc.rc))
                    inventoryd.logmessage(severity="error", message="%s - %s" % (connector["name"], cc.message))
                
            db.endHistoryItem(hid, cc.rc, cc.message)
            inventoryd.logmessage(severity="info", message="Syncing %s done" % connector["name"])
        else:
            inventoryd.logmessage(severity="info", message="Could not start %s sync" % connector["name"])
        
        db.disconnect()
        
        self._createInventoryCacheFile()
        
    def _createInventoryCacheFile(self):
        inventoryd.logmessage(severity="info", message="Create Inventory cache file")
        inventoryd.logmessage(severity="info", message="Generating Ansible Inventory")
        db = inventoryd.db(self._cfg["db"])
        res = db.getAnsibleInventory()
        db.disconnect()
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
        filename = "%s/%s.json" % (self._cli.cachefilepath, timestamp)
        inventoryd.logmessage(severity="info", message="Creating cache file %s" % filename)
        with open(filename, "w") as f:
            f.write(json.dumps(res, sort_keys=True, indent=4, separators=(',',': ')))
        
        inventoryd.logmessage(severity="info", message="Creating link to %s" % filename)
        if os.path.isfile("%s/latest.json" % self._cli.cachefilepath) is True:
            os.unlink("%s/latest.json" % self._cli.cachefilepath)
        os.symlink(filename,"%s/latest.json" % self._cli.cachefilepath)
        
        inventoryd.logmessage(severity="info", message="Done generating Ansible Inventory")
        
    def _startRESTserver(self):
        inventoryd.logmessage(severity="info", message="Starting the REST server")
        self._startHTTPRESTserver()
        self._startHTTPSRESTserver()
        
        
    def _startHTTPRESTserver(self):
        self._http_restserver = inventoryd.RESTserver(self._cfg["rest_server"]["listen"], int(self._cfg["rest_server"]["http_port"]))
        self._http_restserver.start()
    
    def _startHTTPSRESTserver(self):
        self._https_restserver = inventoryd.RESTserver(self._cfg["rest_server"]["listen"], int(self._cfg["rest_server"]["https_port"]),self._cfg["rest_server"]["ssl_certificate"],self._cfg["rest_server"]["ssl_keyfile"])
        self._https_restserver.start()
    
    def _stopRESTserver(self):
        inventoryd.logmessage(severity="info", message="Stopping the REST server")
        if self._http_restserver is not None:
            self._http_restserver.stop()
        if self._https_restserver is not None:
            self._https_restserver.stop()

