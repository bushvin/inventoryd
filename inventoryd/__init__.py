from restserver import RESTserver
from getconfig import getconfig
from getcliargs import getcliargs
from db import db
from db_sqlite3 import db_sqlite3
from connector import connector
from connector_uri import connector_uri
from logmessage import logmessage
from daemon import daemon

class localData(object):
    cfg = {}
    cli = {}

class inventory():
    def __ini__(self):
        obj = { 'message':'Hello, World' }
        return obj

    def getOBJ(self):
        hostvars = dict()
        groups = dict()
        res = { '_meta': { 'hostvars': {} } }
        tdb = db(localData.cfg["db"])

        for el in tdb.getHostCache():
            try:
                hostvars[el["hostname"]]
            except:
                hostvars[el["hostname"]] = dict()
            
            hostvars[el["hostname"]].update({ el["fact"]:el["value"] })
        res["_meta"]["hostvars"] = hostvars
        
        tgc = tdb.getGroupCache()
        for el in tgc["vars"]:
            try:
                groups[el["groupname"]]
            except:
                groups[el["groupname"]] = {'vars':{}}
            
            groups[el["groupname"]]["vars"].update({ el["fact"]:el["value"] })

        for el in tgc["membership"]: 
            try:
                groups[el["groupname"]]
            except:
                groups[el["groupname"]] = dict()
            
            if el["childtype"] == "host":
                try:
                    groups[el["groupname"]]["hosts"]
                except:
                    groups[el["groupname"]]["hosts"] = []
                
                groups[el["groupname"]]["hosts"].append(el["childname"])
            elif el["childtype"] == "group":
                try:
                    groups[el["groupname"]]["children"]
                except:
                    groups[el["groupname"]]["children"] = []
                
                groups[el["groupname"]]["children"].append(el["childname"])
        res.update(groups)
        if localData.cfg["inventory"]["create_all"] is True:
            res["all"] = [ el for el in res["_meta"]["hostvars"] ]
        if localData.cfg["inventory"]["create_localhost"] is True:
            res["_meta"]["hostvars"]["localhost"] = { 'ansible_connection': localData.cfg["inventory"]["localhost_connection"] }
        tdb.disconnect()
        return res
