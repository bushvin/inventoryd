import inventoryd
import inventoryd.connector_uri as connector_uri
from threading import Timer
import os
import sys
from threading import Thread

class daemon:
    _cfg = None
    _cli = None
    _https_restserver = None
    _http_restserver = None
    
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
        #self._createPID()
        self._startHousekeeper()
        self._startConnectorSync()
        self._startRESTserver()

    def stop(self, force = False):
        self._stopHousekeeper()
        self._stopConnectorSync()
        self._stopRESTserver()
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
            

        
    def _startHousekeeper(self):
        interval = int(self._cfg["housekeeper"]["frequency"]) * 60
        inventoryd.logmessage(severity="info", message="Starting housekeeping timer")
        inventoryd.logmessage(severity="info", message="Housekeeping frequency: once every %d seconds" % interval)
        self._runHousekeeper()

    def _stopHousekeeper(self):
        inventoryd.logmessage(severity="info", message="Stopping the housekeeper timer")
        self._HouseKeeperTimer.cancel()
    
    def _runHousekeeper(self):
        inventoryd.logmessage(severity="info", message="Starting Housekeeping run")
        interval = int(self._cfg["housekeeper"]["frequency"]) * 60
        self._HouseKeeperTimer = Timer(interval, self._runHousekeeper)
        self._HouseKeeperTimer.start()

        db = inventoryd.db(self._cfg["db"])
        id_list = db.deleteHistory(self._cfg["housekeeper"]["history"])
        db.disconnect()

        inventoryd.logmessage(severity="info", message="Ending Housekeeping run")


        
    def _startConnectorSync(self):
        interval = int(self._cfg["connector_sync"]["frequency"]) * 60
        inventoryd.logmessage(severity="info", message="Starting Connector Sync timer")
        inventoryd.logmessage(severity="info", message="Connector Sync frequency: once every %d seconds" % interval)
        self._runConnectorySync()
    
    def _stopConnectorSync(self):
        inventoryd.logmessage(severity="debug", message="Stopping the Connector sync timer")
        self._ConnectorSyncTimer.cancel()

    def _runConnectorySync(self):
        inventoryd.logmessage(severity="info", message="Starting the Connector Sync run")
        interval = int(self._cfg["connector_sync"]["frequency"]) * 60
        self._ConnectorSyncTimer = Timer(interval, self._runConnectorySync)
        self._ConnectorSyncTimer.start()
        
        db = inventoryd.db(self._cfg["db"])
        connectors = db.getConnectors()
        for c in connectors:
            hid = db.startHistoryItem(c["id"])
            
            try:
                exec "connector_%s" % c["connector"]
            except:
                libpath = self._cfg["inventoryd"]["connector_path"]
                
                inventoryd.logmessage(severity="debug", message="Connector %s hasn't been imported yet. Attempting." % c["connector"])
                execute_connector = False
                
                if libpath is not None and os.path.isdir(self._cfg["inventoryd"]["connector_path"]):
                    inventoryd.logmessage(severity="debug", message="inventoryd.connector_path is set and connector library exists!")
                    try:
                        exec "import connector_%s" % c["connector"]
                    except:
                        inventoryd.logmessage(severity="crit", message="Could not import the connector %s" % c["connector"])
                    else:
                        exec "import connector_%s" % c["connector"]
                        execute_connector = True
                        
                elif libpath is not None:
                    inventoryd.logmessage(severity="err", message="inventoryd.connector_path is set but connector library doesn't exist!")
                elif libpath is None:
                    inventoryd.logmessage(severity="debug", message="inventoryd.connector_path is not set")
            else:
                execute_connector = True
            
            if execute_connector is True:
                inventoryd.logmessage(severity="info", message="Syncing %s" % c["name"])
                exec "cc = connector_%s(c['parameters'])" % c["connector"]
                if c["type"] == "hosts":
                    facts = cc.getHosts()
                    if cc.rc == 0:
                        inventoryd.logmessage(severity="info", message="%s - synchronizing %d hostvar facts" % (c["name"], len(facts)))
                        db.commitHostsCache(hid,facts)
                        inventoryd.logmessage(severity="info", message="%s - %d hostvar facts synchronized" % (c["name"], len(facts)))
                    else:
                        inventoryd.logmessage(severity="error", message="%s - An error occurred synchronizing hostvars. RC:%d" % (c["name"],cc.rc))
                        inventoryd.logmessage(severity="error", message="%s - %s" % (c["name"],cc.message))
                else:
                    facts, hosts, children = cc.getGroups()
                    if cc.rc == 0:
                        inventoryd.logmessage(severity="info", message="%s - synchronizing %d groupvar facts" % (c["name"], len(facts)))
                        inventoryd.logmessage(severity="info", message="%s - synchronizing %d group host memberships" % (c["name"], len(hosts)))
                        inventoryd.logmessage(severity="info", message="%s - synchronizing %d group group memberships" % (c["name"], len(children)))
                        db.commitGroupsCache(hid,facts, hosts, children)
                        inventoryd.logmessage(severity="info", message="%s - %d groupvar facts synchronized" % (c["name"], len(facts)))
                        inventoryd.logmessage(severity="info", message="%s - %d group host memberships synchronized" % (c["name"], len(hosts)))
                        inventoryd.logmessage(severity="info", message="%s - %d group group memberships synchronized" % (c["name"], len(children)))
                    else:
                        inventoryd.logmessage(severity="error", message="%s - An error occurred synchronizing groups. RC:%d" % (c["name"], cc.rc))
                        inventoryd.logmessage(severity="error", message="%s - %s" % (c["name"], cc.message))
                    
                db.endHistoryItem(hid, cc.rc, cc.message)
                inventoryd.logmessage(severity="info", message="Syncing %s done" % c["name"])
            else:
                inventoryd.logmessage(severity="info", message="Could not start %s sync" % c["name"])
            
        db.disconnect()
        inventoryd.logmessage(severity="info", message="Ending the Connector Sync run")


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

