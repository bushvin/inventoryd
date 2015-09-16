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
import sys
import json

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
        
        self.connect()
    
    def connect(self):
        inventoryd.logmessage(severity="DEBUG", message="Connecting to database.")
        if self._dbo.connect() is True:
            return True
        else:
            inventoryd.logmessage(severity="crit", message="Cannot connect to database. Aborting.")
            sys.exit(1)
    
    def disconnect(self):
        inventoryd.logmessage(severity="DEBUG", message="Disconnecting from database.")
        if self._dbo.disconnect() is True:
            return True
        else:
            inventoryd.logmessage(severity="crit", message="Cannot disconnect from database. Aborting.")
            sys.exit(1)
        
    def query(self, query):
        inventoryd.logmessage(severity="DEBUG", message="Execute query %s" % query)
        res = self._dbo.query(query)
        if res is None:
            inventoryd.logmessage(severity="warn", message="The query encountered an error.")
        
        return res
    
    def commit(self, query):
        inventoryd.logmessage(severity="DEBUG", message="Committing query %s" % query)
        res = self._dbo.commit(query)
        
        if res is False:
            inventoryd.logmessage(severity="warn", message="The query encountered an error.")
        return res
    
    def getConnector(self, connector_id):
        inventoryd.logmessage(severity="DEBUG", message="Get connector with id %d" % connector_id)
        res = self._dbo.getConnector(connector_id)
        if res is not None:
            res["parameters"] = json.loads(res["parameters"])
        
        return res
        
    def getConnectors(self, enabled = True):
        if enabled is True:
            inventoryd.logmessage(severity="DEBUG", message="Get all connectors")
        else:
            inventoryd.logmessage(severity="DEBUG", message="Get all enabled connectors")
        res = self._dbo.getConnectors(enabled)
        
        for row in res:
            row["parameters"] = json.loads(row["parameters"])
        return res
    
    def getUsers(self, enabled = True):
        inventoryd.logmessage(severity="DEBUG", message="Get all users")
        res = self._dbo.getUsers(enabled)
        return res

    def getUserInfo(self, username = None):
        if username is None:
            inventoryd.logmessage(severity="error", message="Invalid username for user info")
            return None
        else:
            inventoryd.logmessage(severity="DEBUG", message="Get user info for %s" % user)
        res = self._dbo.getUserInfo(username)
        return res
    
    def getRoles(self):
        inventoryd.logmessage(severity="DEBUG", message="Get all roles")
        res = self._dbo.getRoles()
        return res
    
    def getRoleInfo(self, role_name = None):
        if role_name is None:
            inventoryd.logmessage(severity="error", message="Invalid role_name for role info")
            return None
        else:
            inventoryd.logmessage(severity="DEBUG", message="Get role info for %s" % role_name)
        res = self.getRoleInfo(role_name)
        return res
    
    def getRoleMembers(self, role_name = None):
        if role_name is None:
            inventoryd.logmessage(severity="error", message="Invalid role_name for role members")
            return []
        else:
            inventoryd.logmessage(severity="DEBUG", message="Get role members for %s" % role_name)
        res = self._dbo.getRoleMembers(role_name)
        return res
    
    def getRoleACL(self, role_name = None):
        if role_name is None:
            inventoryd.logmessage(severity="error", message="Invalid role_name for role ACL")
            return []
        else:
            inventoryd.logmessage(severity="DEBUG", message="Get role ACLs for %s" % role_name)
        res = self._dbo.getRoleACL(role_name)
        return res
        
    def startHistoryItem(self, connector_id):
        inventoryd.logmessage(severity="DEBUG", message="Start history item for connector id %d" % connector_id)
        res = self._dbo.startHistoryItem(connector_id)
        return res
            
    def endHistoryItem(self, history_id, rc, msg):
        inventoryd.logmessage(severity="DEBUG", message="Ending history item for history id %d" % history_id)
        res = self._dbo.endHistoryItem(history_id, rc, msg)
        if res is False:
            inventoryd.logmessage(severity="error", message="Connectory history item could not be ended.")
        return res
        
    def commitHostsCache(self, history_id, facts):
        inventoryd.logmessage(severity="DEBUG", message="Committing host connector facts to cache")
        res = self._dbo.commitHostsCache(history_id, facts)
        if res is False:
            inventoryd.logmessage(severity="error", message="Host connector cache has not been (fully) comitted.")
        return res
    
    def commitGroupsCache(self, history_id, facts, hosts, children):
        inventoryd.logmessage(severity="DEBUG", message="Committing group connector facts to cache")
        res = self._dbo.commitGroupsCache(history_id, facts, hosts, children)
        if res is False:
            inventoryd.logmessage(severity="error", message="Group connector cache has not been (fully) comitted.")
        return res

    def deleteHistory(self, keep_history):
        inventoryd.logmessage(severity="DEBUG", message="deleting history from cache")
        res = self._dbo.deleteHistory(keep_history)
        if res is False:
            inventoryd.logmessage(severity="error", message="Something went wrong deleting history.")
        return res
        
    def getConnectorHostCache(self, connector_id, timestamp = None):
        inventoryd.logmessage(severity="DEBUG", message="Get hostcache for connector %d" % connector_id)
        res = self._dbo.getConnectorHostCache(connector_id, timestamp)
        if res is False:
            inventoryd.logmessage(severity="error", message="Something went wrong getting the connector hostcache.")
            res = { "vars":[] }
        return res
        
    def getStaticHostCache(self):
        inventoryd.logmessage(severity="DEBUG", message="Get static hostcache")
        res = self._dbo.getStaticHostCache()
        if res is False:
            inventoryd.logmessage(severity="error", message="Something went wrong getting the static hostcache.")
            res = { "vars":[] }
        return res
        
    def getConnectorGroupCache(self, connector_id, timestamp = None):
        inventoryd.logmessage(severity="DEBUG", message="Get groupcache for connector %d" % connector_id)
        res = self._dbo.getConnectorGroupCache(connector_id, timestamp)
        if res is None:
            inventoryd.logmessage(severity="error", message="Something went wrong getting the connector groupcache.")
            res = { "vars":[], 'membership': [] }
        return res

    def getStaticGroupCache(self):
        inventoryd.logmessage(severity="DEBUG", message="Get static groupcache")
        res = self._dbo.getStaticGroupCache()
        if res is None:
            inventoryd.logmessage(severity="error", message="Something went wrong getting the static groupcache.")
            res = { "vars":[], 'membership': [] }
        return res

    def getHostCache(self):
        inventoryd.logmessage(severity="DEBUG", message="Get all host information")
        connectors = sorted(self.getConnectors(True), key=lambda k: k["priority"])
        
        hostscache = { "vars": dict() }
        for c in connectors:
            if c["type"] == "hosts":
                cache = self.getConnectorHostCache(c["id"])
                for c_el in cache["vars"]:
                    index = "%s::%s" % (cache["vars"][c_el]["hostname"], cache["vars"][c_el]["fact"])
                    try:
                        hostscache["vars"][index]
                    except:
                        hostscache["vars"][index] = dict()
                    
                    hostscache["vars"][index]["hostname"] = cache["vars"][c_el]["hostname"]
                    hostscache["vars"][index]["fact"] = cache["vars"][c_el]["fact"]
                    hostscache["vars"][index]["value"] = cache["vars"][c_el]["value"]
                    hostscache["vars"][index]["priority"] = cache["vars"][c_el]["priority"]

        staticcache = self.getStaticHostCache()
        for s_el in staticcache["vars"]:
            index = "%s::%s" % (staticcache["vars"][s_el]["hostname"], staticcache["vars"][s_el]["fact"])
            try:
                hostscache[index]
            except:
                hostscache[index] = dict()
            
            try:
                hostscache[index]["priority"]
            except:
                hostscache[index]["priority"] = 0
            
            if staticcache["vars"][s_el]["priority"] > hostscache["vars"][index]["priority"]:
                hostscache["vars"][index]["hostname"] = staticcache["vars"][s_el]["hostname"]
                hostscache["vars"][index]["fact"] = staticcache["vars"][s_el]["fact"]
                hostscache["vars"][index]["value"] = staticcache["vars"][s_el]["value"]
                hostscache["vars"][index]["priority"] = staticcache["vars"][s_el]["priority"]
            
        return hostscache
    
    def getGroupCache(self):
        inventoryd.logmessage(severity="DEBUG", message="Get all group information")
        connectors = sorted(self.getConnectors(True), key=lambda k: k["priority"])
        
        groupcache = { 'vars': dict(), 'membership':dict() }
        
        for c in connectors:
            cache = self.getConnectorGroupCache(c["id"])
            if c["type"] == "groups":
                for c_el in cache["vars"]:
                    index = "%s::%s" % (cache["vars"][c_el]["groupname"], cache["vars"][c_el]["fact"])
                    try:
                        groupcache["membership"][index]
                    except:
                        groupcache["membership"][index] = dict()
                    
                    groupcache["vars"][index]["groupname"] = cache["vars"][c_el]["groupname"]
                    groupcache["vars"][index]["fact"] = cache["vars"][c_el]["fact"]
                    groupcache["vars"][index]["value"] = cache["vars"][c_el]["value"]
                    groupcache["vars"][index]["priority"] = cache["vars"][c_el]["priority"]

                for c_el in cache["membership"]:
                    index = "%s::%s::%s" % (cache["membership"][c_el]["groupname"], cache["membership"][c_el]["childname"], cache["membership"][c_el]["childtype"])
                    try:
                        groupcache["membership"][index]
                    except:
                        groupcache["membership"][index] = dict()
                    
                    groupcache["membership"][index]["groupname"] = cache["membership"][c_el]["groupname"]
                    groupcache["membership"][index]["childname"] = cache["membership"][c_el]["childname"]
                    groupcache["membership"][index]["childtype"] = cache["membership"][c_el]["childtype"]
                    groupcache["membership"][index]["priority"] = cache["membership"][c_el]["priority"]
                    groupcache["membership"][index]["apply_to_hosts"] = cache["membership"][c_el]["apply_to_hosts"]
                    groupcache["membership"][index]["include_hosts"] = cache["membership"][c_el]["include_hosts"]
                    
        staticcache = self.getStaticGroupCache()
        for s_el in staticcache["vars"]:
            index = "%s::%s" % (staticcache["vars"][s_el]["groupname"], staticcache["vars"][s_el]["fact"])
            try:
                groupcache["vars"][index]
            except:
                groupcache["vars"][index] = dict()
            
            try:
                groupcache["vars"][index]["priority"]
            except:
                groupcache["vars"][index]["priority"] = 0
            
            if staticcache["vars"][s_el]["priority"] > groupcache["vars"][index]["priority"]:
                groupcache["vars"][index]["groupname"] = staticcache["vars"][s_el]["groupname"]
                groupcache["vars"][index]["fact"] = staticcache["vars"][s_el]["fact"]
                groupcache["vars"][index]["value"] = staticcache["vars"][s_el]["value"]
                groupcache["vars"][index]["priority"] = staticcache["vars"][s_el]["priority"]
        
        print cache["membership"]
        for s_el in staticcache["membership"]:
            index = "%s::%s::%s" % (staticcache["membership"][s_el]["groupname"], staticcache["membership"][s_el]["childname"], staticcache["membership"][s_el]["childtype"])
            try:
                groupcache["membership"][index]
            except:
                groupcache["membership"][index] = dict()
            
            try:
                groupcache["membership"][index]["priority"]
            except:
                groupcache["membership"][index]["priority"] = 0
            
            if staticcache["membership"][s_el]["priority"] > groupcache["membership"][index]["priority"]:
                groupcache["membership"][index]["groupname"] = staticcache["membership"][s_el]["groupname"]
                groupcache["membership"][index]["childname"] = staticcache["membership"][s_el]["childname"]
                groupcache["membership"][index]["childtype"] = staticcache["membership"][s_el]["childtype"]
                groupcache["membership"][index]["priority"] = staticcache["membership"][s_el]["priority"]
                groupcache["membership"][index]["apply_to_hosts"] = staticcache["membership"][s_el]["apply_to_hosts"]
                groupcache["membership"][index]["include_hosts"] = staticcache["membership"][s_el]["include_hosts"]
                
        return groupcache

        """
        return self._dbo.getGroupCache()
        """

    def getUserPassword(self, username):
        inventoryd.logmessage(severity="DEBUG", message="Get user passhash for %s" % username)
        res = self._dbo.getUserPassword(username)
        if res is False:
            inventoryd.logmessage(severity="error", message="An error ocurred fetching the passhash.")
            res = [ '','' ]
        return res

    def getUserACL(self, username):
        inventoryd.logmessage(severity="DEBUG", message="Get user ACL for %s" % username)
        res = self._dbo.getUserACL(username)
        if res is False:
            inventoryd.logmessage(severity="error", message="An error ocurred fetching the ACL.")
            res = list()
        return res

    def createConnector(self, name, connector, connector_type, parameters, priority):
        inventoryd.logmessage(severity="DEBUG", message="Create a new connector")
        res = self._dbo.createConnector(name, connector, connector_type, parameters, priority)
        if res is False:
            inventoryd.logmessage(severity="error", message="An error ocurred creating the connector.")

        return res

    def enableConnector(self, connector_id):
        inventoryd.logmessage(severity="DEBUG", message="Enable connector %d" % connector_id)
        res = self._dbo.enableConnector(connector_id)
        if res is False:
            inventoryd.logmessage(severity="error", message="An error ocurred enabling the connector.")

        return res

    def disableConnector(self, connector_id):
        inventoryd.logmessage(severity="DEBUG", message="Disable connector %d" % connector_id)
        res = self._dbo.disableConnector(connector_id)
        if res is False:
            inventoryd.logmessage(severity="error", message="An error ocurred disabling the connector.")

        return res
    
    def readConnector(self, connector_id):
        inventoryd.logmessage(severity="DEBUG", message="Read connector %d" % connector_id)
        res = self._dbo.readConnector(connector_id)
        if res is False:
            inventoryd.logmessage(severity="error", message="An error ocurred reading the connector.")
            res = dict()
        return res

    def getHosts(self):
        inventoryd.logmessage(severity="DEBUG", message="Get host info")
        res = self._dbo.readHost(host_id)
        if res is False:
            inventoryd.logmessage(severity="error", message="An error ocurred getting the hostinfo.")
            res = list()
        return res

    def readHost(self, host_id = None):
        inventoryd.logmessage(severity="DEBUG", message="Get host list")
        res = self._dbo.getHosts()
        if res is False:
            inventoryd.logmessage(severity="error", message="An error ocurred getting the hostlist.")
            res = dict()
        return res
        return self._dbo.readHost(host_id)
    
    def createStaticHostvar(self, hostname = None, fact = None, value = None, priority = 0):
        inventoryd.logmessage(severity="DEBUG", message="Create static hostvar")
        res = self._dbo.createStaticHostvar(hostname, fact, value, priority)
        if res is False:
            inventoryd.logmessage(severity="error", message="An error ocurred creating a static hostvar.")
            res = list()
        return res

    def modifyStaticHostvar(self, hostname = None, fact = None, value = None, priority = -1):
        inventoryd.logmessage(severity="DEBUG", message="Modify static hostvar")
        res = self._dbo.modifyStaticHostvar(hostname, fact, value, priority)
        if res is False:
            inventoryd.logmessage(severity="error", message="An error ocurred modifying a static hostvar.")
            res = list()
        return res

    def deleteStaticHostvar(self, hostname = None, fact = None):
        inventoryd.logmessage(severity="DEBUG", message="Delete static hostvar")
        res = self._dbo.deleteStaticHostvar(hostname, fact)
        if res is False:
            inventoryd.logmessage(severity="error", message="An error ocurred deleting a static hostvar.")
            res = list()
        return res
        
