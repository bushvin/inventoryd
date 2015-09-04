from user import user
from user import acl
from restserver import RESTserver
from getconfig import getconfig
from getcliargs import getcliargs
from db import db
from db_sqlite3 import db_sqlite3
from connector import connector
from connector_uri import connector_uri
from logmessage import logmessage
from daemon import daemon
from jinja2 import Template
import copy
import re

class localData(object):
    cfg = {}
    cli = {}

class inventory():
    def __ini__(self):
        obj = { 'message':'Hello, World' }
        return obj

    def getOBJ(self):
        hosts = dict()
        groups = dict()
        res = { '_meta': { 'hostvars': {} } }
        tdb = db(localData.cfg["db"])

        for el in tdb.getHostCache():
            try:
                hosts[el["hostname"]]
            except:
                hosts[el["hostname"]] = dict()
            
            hosts[el["hostname"]].update({ el["fact"]:el["value"] })
        
        tgc = tdb.getGroupCache()
        for el in tgc["vars"]:
            try:
                groups[el["groupname"]]
            except:
                groups[el["groupname"]] = {'vars':{}}
            
            groups[el["groupname"]]["vars"].update({ el["fact"]:el["value"] })
            try:
                el["apply_to_hosts"]
            except:
                el["apply_to_hosts"] = ".*"

            groups[el["groupname"]]["apply_to_hosts"] = el["apply_to_hosts"]

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
                
            try:
                el["apply_to_hosts"]
            except:
                el["apply_to_hosts"] = ".*"

            groups[el["groupname"]]["apply_to_hosts"] = el["apply_to_hosts"]
            


        groups_rendered = dict()
        for groupname in groups:
            for hostname in hosts:
                if re.match(groups[groupname]["apply_to_hosts"], hostname) is not None:
                    tg = Template(groupname)
                    newgroupname = tg.render(hosts[hostname])
                    group = copy.copy(groups[groupname])
                    del(group["apply_to_hosts"])
                    if groupname != newgroupname:
                        newgroupname = re.sub('\s+','_',newgroupname)
                        try:
                            group["hosts"]
                        except:
                            group["hosts"] = list()
                        group["hosts"].append(hostname)

                    groups_rendered.update( {newgroupname: group} )
                
        res["_meta"]["hostvars"] = hosts
        res.update(groups_rendered)
        if localData.cfg["inventory"]["create_all"] is True:
            res["all"] = [ el for el in res["_meta"]["hostvars"] ]
        if localData.cfg["inventory"]["create_localhost"] is True:
            res["_meta"]["hostvars"]["localhost"] = { 'ansible_connection': localData.cfg["inventory"]["localhost_connection"] }
        tdb.disconnect()
        return res
