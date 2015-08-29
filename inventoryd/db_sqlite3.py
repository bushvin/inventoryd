import sqlite3
import os
import json
import datetime
import inventoryd

class db_sqlite3():
    db_location = None
    
    def __init__(self, conf):
        self.db_location = conf['db_location']
        self.connect()
    
    def connect(self):
        if os.path.isfile(self.db_location) is not True:
            inventoryd.logmessage(severity="crit", message="The database sould not be found")
            sys.exit(1)
        self.connection = sqlite3.connect(self.db_location)
        self.connection.row_factory = sqlite3.Row
        self.cursor = self.connection.cursor()
    
    def disconnect(self):
        self.connection.close()
        
    def query(self, query):
        inventoryd.logmessage(severity="DEBUG", message="Execute query %s" % query)
        try:
            self.cursor.execute(query)
        except:
            inventoryd.logmessage(severity="error", message="An error occurred executing the following query: %s" % query)
            return None
            
        ret = []
        for row in self.cursor.execute(query):
            newrow = {}
            for key in row.keys():
                newrow[key] = row[key]
            ret.append(newrow)
        return ret
    
    def commit(self, query):
        inventoryd.logmessage(severity="DEBUG", message="Committing query %s" % query)
        try:
            self.cursor.execute(query)
        except:
            inventoryd.logmessage(severity="error", message="An error occurred comitting the following query: %s" % query)
            return False
            
        self.connection.commit()
        return True
    
    def getConnectors(self, enabled = True):
        if enabled is True:
            qfilter = "WHERE `enabled`='1'"
        else:
            qfilter = ""
        query = "SELECT * FROM `sync_connector` %s ORDER BY `type`,`priority`;" % qfilter
        res = self.query(query)
        for row in res:
            row["parameters"] = json.loads(row["parameters"])
        return res

    def getUsers(self, enabled = True):
        if enabled is True:
            qfilter = "WHERE `enabled`='1'"
        else:
            qfilter = ""
        query = "SELECT `name` FROM `user` ORDER BY `name`;"
        res = self.query(query)
        return res
    
    def getUserInfo(self, username):
        if isinstance(username, str) is False:
            return None
        query = "SELECT `name` FROM `user` WHERE `name`='%s' LIMIT 0,1;" % username
        res = self.query(query)
        if len(res) == 1:
            return res[0]
        else:
            return None

    def getRoleInfo(self, role_name = None):
        if isinstance(role_name, str) is False:
            return None
        query = "SELECT `name` FROM `role` WHERE `name`='%s' LIMIT 0,1;" % role_name
        res = self.query(query)
        if len(res) == 1:
            return res[0]
        else:
            return None
    
    def getRoleMembers(self, role_name = None):
        if isinstance(role_name, str) is False:
            return []
        query = "SELECT `user_name` FROM `role_member` WHERE `role_name`='%s' ORDER BY `user_name`;" % role_name
        res = self.query(query)
        members = list()
        for el in res:
            members.append(el.user_name)
        
        return members
    
    def getRoleACL(self, role_name):
        if isinstance(role_name, str) is False:
            return []
        query = "SELECT * FROM `acl` WHERE `role_name`='%s' ORDER BY `user_name`;" % role_name
        return self.query(query)
        
    def startHistoryItem(self, connector_id):
        query = "SELECT MAX(`id`) max FROM `sync_history`;"
        res = self.query(query)[0]
        try:
            int(res["max"])
        except:
            next_id = 1
        else:
            next_id = int(res["max"]) + 1
        
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        query = "INSERT INTO `sync_history` (`id`,`connector_id`,`datetime_start`) VALUES('%d', '%d','%s');" % (next_id, connector_id, timestamp)
        self.commit(query)
        return next_id
            
    def endHistoryItem(self, history_id, rc, msg):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        if rc == 0:
            active = 1
        else:
            active = 0
        query = "UPDATE `sync_history` SET `datetime_end`='%s', `active`=%d, `resultcode`=%d, `message`='%s' WHERE `id`='%d';" % (timestamp, active, rc, msg,history_id)
        self.commit(query)
        return True
        
    def commitHostsCache(self, history_id, facts):
        facts_query = list()
        for el in facts:
            facts_query.append("('%d','%s','hostvar','%s','%s')" % (history_id, el["hostname"], el["fact"], json.dumps(el["value"])))
        if len(facts_query) > 0:
            query = "INSERT INTO `cache_vars` (`history_id`,`name`,`type`,`fact`,`value`) VALUES %s;" % ",".join(facts_query)
            self.commit(query)
        return True
    
    def commitGroupsCache(self, history_id, facts, hosts, children):
        facts_query = list()
        for el in facts:
            facts_query.append("('%d','%s','groupvar','%s','%s')" % (history_id, el["groupname"], el["fact"], json.dumps(el["value"])))
        if len(facts_query) > 0:
            query = "INSERT INTO `cache_vars` (`history_id`,`name`,`type`,`fact`,`value`) VALUES %s;" % ",".join(facts_query)
            self.commit(query)
        
        hosts_query = list()
        for el in hosts:
            hosts_query.append("('%d','%s','%s','host')" % (history_id,el["groupname"],el["host"]))
        if len(hosts_query) > 0:
            query = "INSERT INTO `cache_groupmembership` (`history_id`,`name`,`childname`,`childtype`) VALUES %s;" % ",".join(hosts_query)
            self.commit(query)
        
        groups_query = list()
        for el in children:
            groups_query.append("('%d','%s','%s','group')" % (history_id,el["groupname"],el["child"]))
        if len(groups_query) > 0:
            query = "INSERT INTO `cache_groupmembership` (`history_id`,`name`,`childname`,`childtype`) VALUES %s;" % ",".join(groups_query)
            self.commit(query)
                
        return True

    def deleteHistory(self, keep_history):
        connectors = self.getConnectors(False)
        records_deleted = 0
        for conn in connectors:
            all_ids = list()
            del_ids = list()
            query = "SELECT `id` FROM `sync_history` WHERE `connector_id`='%s' ORDER BY `id`;" % conn["id"]
            res = self.query(query)
            if res is not None:
                all_ids = [ str(el["id"]) for el in res ]
                del_ids = all_ids[keep_history:]
                
            if len(del_ids) > 0:
                query = "DELETE FROM `cache_vars` WHERE `history_id` IN (%s);" % ",".join(del_ids)
                changes = self.connection.total_changes
                self.commit(query)
                changes = self.connection.total_changes - changes
                if changes > 0:
                    inventoryd.logmessage(severity="info", message="%s - %d records deleted from vars cache" % (conn["name"], changes))
                
                query = "DELETE FROM `cache_groupmembership` WHERE `history_id` IN (%s);" % ",".join(del_ids)
                changes = self.connection.total_changes
                self.commit(query)
                changes = self.connection.total_changes - changes
                if changes > 0:
                    inventoryd.logmessage(severity="info", message="%s - %d records deleted from group membership cache" % (conn["name"], changes))
                
                query = "DELETE FROM `sync_history` WHERE `id` IN (%s);" % ",".join(del_ids)
                changes = self.connection.total_changes
                self.commit(query)
                changes = self.connection.total_changes - changes
                if changes > 0:
                    inventoryd.logmessage(severity="info", message="%s - %d records deleted from history log" % (conn["name"],changes))
    
    def getConnectorHostCache(self, connector_id, timestamp = None):
        hostcache = { 'vars':[] }
        query = "SELECT `id` FROM `sync_history` WHERE `connector_id`='%d' ORDER BY `id` DESC LIMIT 0,1;" % connector_id
        res = self.query(query)
        if res is not None:
            history_id = int(res[0]["id"])
        else:
            history_id -1
        query = "SELECT * FROM `cache_vars` WHERE `history_id`='%d';" % history_id
        res = self.query(query)
        hostcache["vars"] = [ {'hostname':el["name"], 'fact':el["fact"], 'value':json.loads(el["value"])} for el in res ]

        return hostcache
        
    def getConnectorGroupCache(self, connector_id, timestamp = None):
        groupcache = { 'vars':[], 'membership':[] }
        query = "SELECT `id` FROM `sync_history` WHERE `connector_id`='%d' ORDER BY `id` DESC LIMIT 0,1;" % connector_id
        res = self.query(query)
        if res is not None:
            history_id = int(res[0]["id"])
        else:
            history_id -1
        query = "SELECT * FROM `cache_vars` WHERE `history_id`='%d';" % history_id
        res = self.query(query)
        groupcache["vars"] = [ {'groupname':el["name"], 'fact':el["fact"], 'value':json.loads(el["value"])} for el in res ]
        
        query = "SELECT * FROM `cache_groupmembership` WHERE `history_id`='%d';" % history_id
        res = self.query(query)
        groupcache["membership"] = [ { 'groupname':el['name'], 'childname':el["childname"], 'childtype':el["childtype"] } for el in res ]
            
        return groupcache
        
    def getHostCache(self):
        connectors = sorted(self.getConnectors(True), key=lambda k: k["priority"])
        
        hostscache = []
        for c in connectors:
            if c["type"] == "hosts":
                cache = self.getConnectorHostCache(c["id"])["vars"]
                for c_el in cache:
                    item_found = False
                    for h_el in hostscache:
                        if c_el["hostname"] == h_el["hostname"] and c_el["fact"] == h_el["fact"]:
                             h_el["value"] == c_el["value"]
                             item_found = True
                             break
                    if item_found is False:
                        hostscache.append(c_el)
        
        return hostscache
    
    def getGroupCache(self):
        connectors = sorted(self.getConnectors(True), key=lambda k: k["priority"])
        
        groupcache = { 'vars':[], 'membership':[] }
        for c in connectors:
            if c["type"] == "groups":
                cache = self.getConnectorGroupCache(c["id"])
                #varcache = cache["vars"]
                for c_el in cache["vars"]:
                    item_found = False
                    for h_el in groupcache["vars"]:
                        if c_el["groupname"] == h_el["groupname"] and c_el["fact"] == h_el["fact"]:
                             h_el["value"] == c_el["value"]
                             item_found = True
                             break
                    if item_found is False:
                        groupcache["vars"].append(c_el)

                for c_el in cache["membership"]:
                    item_found = False
                    for h_el in groupcache["membership"]:
                        if c_el["groupname"] == h_el["groupname"] and c_el["childname"] == h_el["childname"] and c_el["childtype"] == h_el["childtype"]:
                             #h_el["value"] == c_el["value"]
                             item_found = True
                             break
                    if item_found is False:
                        groupcache["membership"].append(c_el)
        return groupcache
