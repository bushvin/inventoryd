import inventoryd
import sys

class db():
    _dbo = None
    db_driver = ""
    
    def __init__(self, conf):
        self.db_driver = conf['db_driver']
        inventoryd.logmessage(severity="debug", message="Checking database driver %s." % self.db_driver)
        try:
            exec "inventoryd.db_%s" % self.db_driver
        except:
            inventoryd.logmessage(severity="crit", message="The database driver could not be found! Aborting.")
            sys.exit(1)
        else:
            inventoryd.logmessage(severity="DEBUG", message="Loading database driver %s." % self.db_driver)
            exec "self._dbo = inventoryd.db_%s(conf)" % self.db_driver
    
    def connect(self):
        return self._dbo.connect()
    
    def disconnect(self):
        return self._dbo.disconnect()
        
    def query(self, query):
        return self._dbo.query(query)
    
    def commit(self, query):
        return self._dbo.commit(query)
    
    def getConnectors(self, enabled = True):
        return self._dbo.getConnectors(enabled)
    
    def getUsers(self, enabled = True):
        return self._dbo.getUsers(enabled)

    def getUserInfo(self, username = None):
        return self._dbo.getUserInfo(username)
    
    def getRoles(self):
        return self._dbo.getRoles()
    
    def getRoleInfo(self, role_name = None):
        return self.getRoleInfo(role_name)
    
    def getRoleMembers(self, role_name = None):
        return self._dbo.getRoleMembers(role_name)
    
    def getRoleACL(self, role_name = None):
        return self._dbo.getRoleACL(role_name)
        
    def startHistoryItem(self, connector_id):
        return self._dbo.startHistoryItem(connector_id)
            
    def endHistoryItem(self, history_id, rc, msg):
        return self._dbo.endHistoryItem(history_id, rc, msg)
        
    def commitHostsCache(self, history_id, facts):
        return self._dbo.commitHostsCache(history_id, facts)
    
    def commitGroupsCache(self, history_id, facts, hosts, children):
        return self._dbo.commitGroupsCache(history_id, facts, hosts, children)

    def deleteHistory(self, keep_history):
        return self._dbo.deleteHistory(keep_history)
        
    def getConnectorHostCache(self, connector_id, timestamp = None):
        return self._dbo.getConnectorHostCache(connector_id, timestamp)
        
    def getConnectorGroupCache(self, connector_id, timestamp = None):
        return self._dbo.getConnectorGroupCache(connector_id, timestamp)
        
    def getHostCache(self):
        return self._dbo.getHostCache()
    
    def getGroupCache(self):
        return self._dbo.getGroupCache()

    def getUserPassword(self, username):
        return self._dbo.getUserPassword(username)

    def getUserACL(self, username):
        return self._dbo.getUserACL(username)

    def createConnector(self, name, connector, connector_type, parameters, priority):
        return self._dbo.createConnector(self, name, connector, connector_type, parameters, priority)

    def enableConnector(self, connector_id):
        return self._dbo.enableConnector(connector_id)

    def disableConnector(self, connector_id):
        return self._dbo.disableConnector(connector_id)
    
    def readConnector(self, connector_id):
        return self._dbo.readConnector(connector_id)

    def getHosts(self):
        return self._dbo.getHosts()

    def readHost(self, host_id = None):
        return self._dbo.readHost(host_id)
    
    def createStaticHostvar(self, hostname = None, fact = None, value = None, priority = 0):
        return self._dbo.createStaticHostvar(hostname, fact, value, priority)

    def modifyStaticHostvar(self, hostname = None, fact = None, value = None, priority = -1):
        return self._dbo.modifyStaticHostvar(hostname, fact, value, priority)

    def deleteStaticHostvar(self, hostname = None, fact = None):
        return self._dbo.deleteStaticHostvar(hostname, fact)
        