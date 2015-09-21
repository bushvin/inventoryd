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

import sqlite3
import os
import json
import datetime
import inventoryd

class db_sqlite3():
    db_location = None
    
    def __init__(self, conf):
        self.db_location = conf['db_location']
        #self.connect()
    
    def connect(self):
        if os.path.isfile(self.db_location) is not True:
            inventoryd.logmessage(severity="crit", message="The database sould not be found")
            return False
        else:
            self.connection = sqlite3.connect(self.db_location)
            self.connection.row_factory = sqlite3.Row
            self.cursor = self.connection.cursor()
            return True
    
    def disconnect(self):
        try:
            self.connection.close()
        except sqlite3.Error as e:
            inventoryd.logmessage(severity="crit", message="Could not disconnect from database: %s" % e.args[0])
            return False
        except:
            inventoryd.logmessage(severity="crit", message="Could not disconnect from database: Unknown error")
            return False
        else:
            return True
        
        
    def query(self, query):
        try:
            self.cursor.execute(query)
        except:
            inventoryd.logmessage(severity="error", message="An error occurred executing the following query: %s" % query)
            return None
            
        ret = []
        for row in self.cursor.execute(query):
            ret.append(dict(zip(row.keys(), row)))
        self.result_count = len(ret)
        return ret
    
    def commit(self, query):
        
        try:
            self.cursor.execute(query)
        except sqlite3.Error as e:
            inventoryd.logmessage(severity="error", message="A sqlite3 error occurred: %s" % e.args[0])
            inventoryd.logmessage(severity="error", message="An error occurred comitting the following query: %s" % query)
            return False
        except:
            inventoryd.logmessage(severity="error", message="An error occurred comitting the following query: %s" % query)
            return False
            
        self.connection.commit()
        return True
    
    def sanitize(self, value):
        value = value.replace('\'','\'\'')
        return value
    
    def getConnector(self, connector_id):
        query = "SELECT * FROM `sync_connector` WHERE `id`='%d';" % int(connector_id)
        res = self.query(query)
        if len(res) == 1:
            return res[0]
        else:
            return None
    
    def getConnectors(self, enabled = True):
        if enabled is True:
            qfilter = "WHERE `enabled`='1'"
        else:
            qfilter = ""
        query = "SELECT * FROM `sync_connector` %s ORDER BY `type`,`priority`;" % qfilter
        res = self.query(query)
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
        if self.commit(query) is not None:
            return True
        else:
            return False

    def commitHostsCache(self, history_id, facts):
        count = 0
        for el in facts:
            if count == 0:
                query = "INSERT INTO `cache_vars` SELECT '%d' AS `history_id`, '%s' AS `name`, 'hostvar' AS `type`, '%s' AS `fact`, '%s' AS `value`" % (history_id, self.sanitize(el["hostname"]), self.sanitize(el["fact"]), self.sanitize(json.dumps(el["value"])))
            else:
                query = "%s UNION SELECT '%d', '%s','hostvar','%s','%s'" %(query, history_id, self.sanitize(el["hostname"]), self.sanitize(el["fact"]), self.sanitize(json.dumps(el["value"])))
            count = count + 1
            if count == 500:
                if self.commit(query) is None:
                    return False
                count = 0
        
        if count > 0:
            if self.commit(query) is None:
                return False

        return True
    
    def commitGroupsCache(self, history_id, facts, hosts, children):
        count = 0
        for el in facts:
            if count == 0:
                query = "INSERT INTO `cache_vars` SELECT '%d' AS `history_id`, '%s' AS `name`, 'groupvar' AS `type`, '%s' AS `fact`, '%s' AS `value`" % ( history_id, self.sanitize(el["groupname"]), self.sanitize(el["fact"]), self.sanitize(json.dumps(el["value"])))
            else:
                query = "%s UNION SELECT '%d', '%s','groupvar','%s','%s'" %(query, history_id, self.sanitize(el["groupname"]), self.sanitize(el["fact"]), self.sanitize(json.dumps(el["value"])))
            count = count + 1
            if count == 500:
                if self.commit(query) is None:
                    return False
                count = 0
        
        if count > 0:
            if self.commit(query) is None:
                return False

        count = 0
        for el in facts:
            if count == 0:
                query = "INSERT INTO `cache_groupmembership` SELECT '%d' AS `history_id`, '%s' AS `name`, '%s' AS `childname`, 'host' AS `childtype`" % ( history_id, self.sanitize(el["groupname"]), self.sanitize(el["host"]))
            else:
                query = "%s UNION SELECT '%d', '%s','%s','host'" %(query, history_id, self.sanitize(el["groupname"]), self.sanitize(el["host"]))
            count = count + 1
            if count == 500:
                if self.commit(query) is None:
                    return False
                count = 0
        
        if count > 0:
            if self.commit(query) is None:
                return False


        count = 0
        for el in facts:
            if count == 0:
                query = "INSERT INTO `cache_groupmembership` SELECT '%d' AS `history_id`, '%s' AS `name`, '%s' AS `childname`, 'group' AS `childtype`" % ( history_id,el["groupname"], self.sanitize(el["child"]))
            else:
                query = "%s UNION SELECT '%d', '%s','%s','group'" %(query, history_id, self.sanitize(el["groupname"]), self.sanitize(el["child"]))
            count = count + 1
            if count == 500:
                if self.commit(query) is None:
                    return False
                count = 0
        
        if count > 0:
            if self.commit(query) is None:
                return False

        return True

    def deleteHistory(self, keep_history):
        connectors = self.getConnectors(False)
        records_deleted = 0
        for conn in connectors:
            all_ids = list()
            del_ids = list()
            query = "SELECT `id` FROM `sync_history` WHERE `connector_id`='%s' ORDER BY `id`;" % conn["id"]
            res = self.query(query)
            if res is None:
                return False
            
            all_ids = [ str(el["id"]) for el in res ]
            del_ids = all_ids[keep_history:]
                
            if len(del_ids) > 0:
                query = "DELETE FROM `cache_vars` WHERE `history_id` IN (%s);" % ",".join(del_ids)
                changes = self.connection.total_changes
                if self.commit(query) is None:
                    return False
                changes = self.connection.total_changes - changes
                if changes > 0:
                    inventoryd.logmessage(severity="info", message="%s - %d records deleted from vars cache" % (conn["name"], changes))
                
                query = "DELETE FROM `cache_groupmembership` WHERE `history_id` IN (%s);" % ",".join(del_ids)
                changes = self.connection.total_changes
                if self.commit(query) is None:
                    return False
                changes = self.connection.total_changes - changes
                if changes > 0:
                    inventoryd.logmessage(severity="info", message="%s - %d records deleted from group membership cache" % (conn["name"], changes))
                
                query = "DELETE FROM `sync_history` WHERE `id` IN (%s);" % ",".join(del_ids)
                changes = self.connection.total_changes
                if self.commit(query) is None:
                    return False
                changes = self.connection.total_changes - changes
                if changes > 0:
                    inventoryd.logmessage(severity="info", message="%s - %d records deleted from history log" % (conn["name"],changes))
            
            return True
    
    def getConnectorHostCache(self, connector_id, timestamp = None):
        hostcache = { 'vars':[] }
        query = "SELECT `a`.`id`, `b`.`priority` FROM `sync_history` `a` LEFT JOIN `sync_connector` `b` ON (`a`.`connector_id`=`b`.`id`) WHERE `a`.`connector_id`='%d' ORDER BY `a`.`id` DESC LIMIT 0,1;" % connector_id
        res = self.query(query)
        if res is not None:
            history_id = int(res[0]["id"])
            priority = int(res[0]["priority"])
        else:
            return False
            #history_id = -1
            #priority = -1
            
        query = "SELECT * FROM `cache_vars` WHERE `history_id`='%d';" % history_id
        res = self.query(query)
        if res is None:
            return False
        hostcache["vars"] = dict( ( '%s::%s' %(el["name"], el["fact"]), {'hostname':el["name"], 'fact':el["fact"], 'value':json.loads(el["value"]), 'priority': priority}) for el in res )

        return hostcache
    
    def getStaticHostCache(self):
        hostcache = { 'vars':[] }
        query = "SELECT * FROM `static_vars` WHERE `type`='hostvar';"
        res = self.query(query)
        if res is None:
            return False
        hostcache["vars"] = dict( ( '%s::%s' %(el["name"], el["fact"]), {'hostname':el["name"], 'fact':el["fact"], 'value':json.loads(el["value"]), 'priority': int(el["priority"])}) for el in res )
        return hostcache
        
    def getConnectorGroupCache(self, connector_id, timestamp = None):
        groupcache = { 'vars':[], 'membership':[] }
        query = "SELECT `a`.`id`, `b`.`priority` FROM `sync_history` `a` LEFT JOIN `sync_connector` `b` ON (`a`.`connector_id`=`b`.`id`) WHERE `a`.`connector_id`='%d' ORDER BY `a`.`id` DESC LIMIT 0,1;" % connector_id
        res = self.query(query)
        if res is not None:
            history_id = int(res[0]["id"])
            priority = int(res[0]["priority"])
        else:
            return False
            #history_id = -1
            #priority = -1
        
        query = "SELECT * FROM `cache_vars` WHERE `history_id`='%d';" % history_id
        res = self.query(query)
        if res is None:
            return False
        groupcache["vars"] = dict( ( '%s::%s' %(el["name"], el["fact"]), {'groupname':el["name"], 'fact':el["fact"], 'value':json.loads(el["value"]), 'priority': priority}) for el in res )
        
        query = "SELECT * FROM `cache_groupmembership` WHERE `history_id`='%d';" % history_id
        res = self.query(query)
        if res is None:
            return False
        groupcache["membership"] = dict( ( '%s::%s::%s' % (el["name"], el["childname"], el["childtype"]), { 'groupname':el['name'], 'childname':el["childname"], 'childtype':el["childtype"], 'priority': priority, 'apply_to_hosts': '.*', 'include_hosts': True }) for el in res)
            
        return groupcache
    
    def getStaticGroupCache(self):
        groupcache = { 'vars':[], 'membership':[] }
        query = "SELECT * FROM `static_vars` WHERE `type`='groupvar';"
        res = self.query(query)
        groupcache["vars"] = dict( ( '%s::%s' %(el["name"], el["fact"]), {'groupname':el["name"], 'fact':el["fact"], 'value':json.loads(el["value"]), 'priority': int(el["priority"])}) for el in res )

        query = "SELECT * FROM `static_groupmembership`;"
        res = self.query(query)
        
        groupcache["membership"] = dict( ( '%s::%s::%s' % (el["name"], el["childname"], el["childtype"]), { 'groupname':el['name'], 'childname':el["childname"], 'childtype':el["childtype"], 'priority': int(el["priority"]), 'apply_to_hosts': el["apply_to_hosts"], 'include_hosts': el["include_hosts"] }) for el in res)
        
        return groupcache
    
    def getUserPassword(self, username):
        query = "SELECT `passhash` FROM `user` WHERE `name`='%s' LIMIT 0,1;" % username
        res = self.query(query)
        if res is None:
            return False
        return res[0]["passhash"].split(':')
    
    def getUserACL(self, username):
        query = "SELECT `b`.`object`,`b`.`ace_list`,`b`.`ace_read`,`b`.`ace_create`,`b`.`ace_modify`,`b`.`ace_delete` FROM `role_member` `a` LEFT JOIN `acl` `b` ON (`a`.`role_name`=`b`.`role_name`) WHERE `a`.`user_name`='%s'; " % username
        
        return self.query(query)

    def createConnector(self, name, connector, connector_type, schedule, parameters, priority):
        query = "SELECT MAX(`id`) `connector_id` FROM `sync_connector`;"
        res = self.query(query)
        if res is None:
            return False
        elif len(res) == 1 and res[0]["connector_id"] is not None:
            connector_id = int(res[0]["connector_id"]) + 1
        else:
            connector_id = 1
        query = "INSERT INTO `sync_connector` (`id`) VALUES('%d');" % connector_id
        #print query
        if self.commit(query) is None:
            return -1
        
        return connector_id
        
    def modifyConnector(self, connector_id, name = None, connector = None, connector_type = None, schedule = "@daily", parameters = None, priority = None):
        query_args = list()
        if name is not None:
            query_args.append("`name`='%s'" % name)
        
        if connector is not None:
            query_args.append("`connector`='%s'" % connector)
        
        if connector_type is not None:
            query_args.append("`type`='%s'" % connector_type)
        
        if parameters is not None and isinstance(parameters, dict):
            query_args.append("`parameters`='%s'" % json.dumps(parameters))
        
        if priority is not None:
            query_args.append("`priority`='%d'" % int(priority))
        
        query_args.append("`schedule`='%s'" % schedule)
        if len(query_args) > 0:
            query = "UPDATE `sync_connector` SET %s WHERE `id`=%d;" % (", ".join(query_args), int(connector_id))
            return self.commit(query)
        
        return True

    def enableConnector(self, connector_id):
        query = "UPDATE `sync_connector` SET `enabled`=1 WHERE `id`=%d" % int(connector_id)
        return self.commit(query)
                
    def disableConnector(self, connector_id):
        query = "UPDATE `sync_connector` SET `enabled`=0 WHERE `id`=%d" % int(connector_id)
        return self.commit(query)
    
    def readConnector(self, connector_id):
        query = "SELECT * FROM `sync_connector` WHERE `id`=%d LIMIT 0,1;" % int(connector_id)
        res = self.query(query)
        if res is None:
            return False
        elif len(res) == 1:
            return res[0]
        else:
            return dict()

    def getHosts(self):
        res = []
        query = "SELECT * FROM `sync_connector` WHERE `enabled`=1;"
        connections = self.query(query)
        if connections is None:
            return False
        
        for conn in connections:
            query = "SELECT * FROM `sync_history` WHERE `connector_id`=%d AND `active`=1 ORDER BY `datetime_end` DESC LIMIT 0,1;" % int(conn["id"])
            history = self.query(query)
            if history is None:
                return False
            for hist in history:
                query = "SELECT `name` FROM `cache_vars` WHERE `history_id`=%d GROUP BY `name` ORDER BY `name`;" % int(hist["id"])
                hostlist = self.query(query)
                if hostlist is None:
                    return False
                for hostname in hostlist:
                    host_found = False
                    for el in res:
                        if el["hostname"] == hostname["name"]:
                            host_found = True
                            break
                    if host_found is False:
                        res.append({'hostname':hostname["name"], 'id':hostname["name"]})
                
        query = "SELECT `name` FROM `static_vars` WHERE `type`='hostvar' GROUP BY `name` ORDER BY `name`;"
        varlist = self.query(query)
        if varlist is None:
            return False
        for row in varlist:
            for el in res:
                if el["hostname"] == row["name"]:
                    host_found = True
                    break
            if host_found is False:
                res.append({'hostname':row["name"], 'id':row["name"]})
        return res

    def readHost(self, host_id = None):
        res = dict()
        query = "SELECT * FROM `sync_connector` WHERE `enabled`=1;"
        connections = self.query(query)
        if connections is None:
            return False
        for conn in connections:
            query = "SELECT * FROM `sync_history` WHERE `connector_id`=%d AND `active`=1 ORDER BY `datetime_end` DESC LIMIT 0,1;" % int(conn["id"])
            history = self.query(query)
            if history is None:
                return False
            for hist in history:
                query = "SELECT * FROM `cache_vars` WHERE `name`='%s' AND `type`='hostvar' AND `history_id`='%d' ORDER BY `fact`;" % (host_id, int(hist["id"]))
                varlist = self.query(query)
                if varlist is None:
                    return False
                for el in varlist:
                    try:
                        res[el["fact"]]
                    except:
                        res[el["fact"]] = list()
                    
                    res[el["fact"]].append({'value':json.loads(el["value"]), 'priority':conn["priority"], 'source':'connector', 'connector_id':conn["id"]})
        query = "SELECT * FROM `static_vars` WHERE `name`='%s' AND `type`='hostvar' ORDER BY `fact`;" % host_id
        varlist = self.query(query)
        if varlist is None:
            return False
        for el in varlist:
            try:
                res[el["fact"]]
            except:
                res[el["fact"]] = list()
            
            res[el["fact"]].append({'value':json.loads(el["value"]), 'priority':el["priority"], 'source':'static'})
        return res
    
    def createStaticHostvar(self, hostname = None, fact = None, value = None, priority = 0):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        query = "INSERT INTO `static_vars` (`created`, `name`, `type`, `fact`, `value`, `priority`) VALUES('%s', '%s', 'hostvar', '%s', '%s', '%d');" % (timestamp, hostname, fact, json.dumps(value,separators=(',',': ')), priority)
        return self.commit(query)

    def modifyStaticHostvar(self, hostname = None, fact = None, value = None, priority = -1):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        query_filter = list()
        if value is not None:
            query_filter.append("`value`='%s'" % json.dumps(value,separators=(',',': ')))
        if priority >= 0:
            query_filter.append("`priority`='%d'" % priority)
         
        if len(query_filter) > 0:
            query = "UPDATE `static_vars` SET %s WHERE `type`='hostvar' AND `name`='%s' AND `fact`='%s';" % ( ", ".join(query_filter), hostname, fact)
            if self.commit(query) is None:
                return False
        
        return True

    def deleteStaticHostvar(self, hostname = None, fact = None):
        query = "DELETE FROM `static_vars` WHERE `name`='%s' AND `fact`='%s' AND `type`='hostvar';" % (hostname, fact)
        return self.commit(query)

    def deleteConnector(self, connector_id):
        query = "DELETE FROM `sync_connector` WHERE `id`='%d';" % connector_id
        if self.commit(query) is None:
            return False
        return True
