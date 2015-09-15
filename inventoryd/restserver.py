from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from SocketServer import ThreadingMixIn
import threading
import re
import inventoryd
import json
import ssl
import inventoryd
from jinja2 import Template
import copy


def showInventory(user = None, payload = None, handler = None):
    inventoryd.logmessage(severity="debug", message="Inventory pull request")
    handler.send_response(200)
    handler.send_header('Content-Type', 'application/json')
    handler.end_headers()
    

    hosts = dict()
    groups = dict()
    res = { '_meta': { 'hostvars': {} } }
    tdb = inventoryd.db(inventoryd.localData.cfg["db"])
    
    inventoryd.logmessage(severity="debug", message="creating hostvars - begin")
    thc = tdb.getHostCache()["vars"]
    
    for el in thc:
        try:
            hosts[thc[el]["hostname"]]
        except:
            hosts[thc[el]["hostname"]] = dict()
        
        hosts[thc[el]["hostname"]].update({ thc[el]["fact"]:thc[el]["value"] })
    
    inventoryd.logmessage(severity="debug", message="creating hostvars - end")
    
    inventoryd.logmessage(severity="debug", message="creating groupvars - begin")

    tgc = tdb.getGroupCache()

    for el in tgc["vars"]:
        try:
            groups[tgc["vars"][el]["groupname"]]
        except:
            groups[tgc["vars"][el]["groupname"]] = {'vars':{}}
        
        groups[tgc["vars"][el]["groupname"]]["vars"].update({ tgc["vars"][el]["fact"]:tgc["vars"][el]["value"] })
        
        groups[tgc["vars"][el]["groupname"]]["apply_to_hosts"] = tgc["vars"][el]["apply_to_hosts"]

    for el in tgc["membership"]: 
        try:
            groups[tgc["membership"][el]["groupname"]]
        except:
            groups[tgc["membership"][el]["groupname"]] = dict()
        
        if tgc["membership"][el]["childtype"] == "host":
            try:
                groups[tgc["membership"][el]["groupname"]]["hosts"]
            except:
                groups[tgc["membership"][el]["groupname"]]["hosts"] = []
            
            groups[tgc["membership"][el]["groupname"]]["hosts"].append(tgc["membership"][el]["childname"])
        elif tgc["membership"][el]["childtype"] == "group":
            try:
                groups[tgc["membership"][el]["groupname"]]["children"]
            except:
                groups[tgc["membership"][el]["groupname"]]["children"] = []
            groups[tgc["membership"][el]["groupname"]]["children"].append(tgc["membership"][el]["childname"])
        
        groups[tgc["membership"][el]["groupname"]]["apply_to_hosts"] = tgc["membership"][el]["apply_to_hosts"]
        groups[tgc["membership"][el]["groupname"]]["include_hosts"] = tgc["membership"][el]["include_hosts"]
        groups[tgc["membership"][el]["groupname"]]["childtype"] = tgc["membership"][el]["childtype"]
        groups[tgc["membership"][el]["groupname"]]["childname"] = tgc["membership"][el]["childname"]
        
    inventoryd.logmessage(severity="debug", message="creating groupvars - end")

    inventoryd.logmessage(severity="debug", message="rendering groups - begin")
    groups_rendered = dict()
    for groupname in groups:
        try:
            groups[groupname]["hosts"]
        except:
            groups[groupname]["hosts"] = list()

        try:
            groups[groupname]["children"]
        except:
            groups[groupname]["children"] = list()

        for hostname in hosts:
            if re.match(groups[groupname]["apply_to_hosts"], hostname) is not None:
                tg = Template(groupname)
                newgroupname = tg.render(hosts[hostname])
                newgroupname = re.sub('\s+','_',newgroupname)
            else:
                newgroupname = groupname
            
            try:
                groups_rendered[newgroupname]
            except:
                groups_rendered[newgroupname] = dict()
            
            try:
                groups_rendered[newgroupname]["hosts"]
            except:
                groups_rendered[newgroupname]["hosts"] = list()
                
            try:
                groups_rendered[newgroupname]["children"]
            except:
                groups_rendered[newgroupname]["children"] = list()
            
            if groups[groupname]["include_hosts"] == 1 and groups[groupname]["childtype"] == "host" and groups[groupname]["childname"] not in groups_rendered[newgroupname]["hosts"]:
                groups_rendered[newgroupname]["hosts"].append(groups[groupname]["childname"])
            elif groups[groupname]["childtype"] == "group":
                tc = Template(groups[groupname]["childname"])
                childgroupname = tc.render(hosts[hostname])
                childgroupname = re.sub('\s+','_',childgroupname)
                if childgroupname not in groups_rendered[newgroupname]["children"]:
                    groups_rendered[newgroupname]["children"].append(childgroupname)
                try:
                   groups_rendered[childgroupname]
                except:
                    groups_rendered[childgroupname] = { 'hosts':[], 'children':[] }
            
            if groups[groupname]["include_hosts"] == 1 :
                groups_rendered[newgroupname]["hosts"].append(hostname)
                
                        
    inventoryd.logmessage(severity="debug", message="rendering groups - end")
            
    res["_meta"]["hostvars"] = hosts
    for el in groups_rendered:
        if len(groups_rendered[el]["hosts"]) == 0:
            del(groups_rendered[el]["hosts"])
        else:
            groups_rendered[el]["hosts"] = list(set(groups_rendered[el]["hosts"]))
            groups_rendered[el]["hosts"].sort()
            
        if len(groups_rendered[el]["children"]) == 0:
            del(groups_rendered[el]["children"])
        else:
            groups_rendered[el]["children"] = list(set(groups_rendered[el]["children"]))
            groups_rendered[el]["children"].sort()
            
    res.update(groups_rendered)
    if inventoryd.localData.cfg["inventory"]["create_all"] is True:
        res["all"] = { 'hosts': list(set([ el for el in res["_meta"]["hostvars"] ])) }
        res["all"]["hosts"].sort()
    if inventoryd.localData.cfg["inventory"]["create_localhost"] is True:
        res["_meta"]["hostvars"]["localhost"] = { 'ansible_connection': inventoryd.localData.cfg["inventory"]["localhost_connection"] }
    tdb.disconnect()
    
    
    
    handler.wfile.write(json.dumps(res, sort_keys=True, indent=4, separators=(',',': ')))
    return True

def listConnectors(user = None, payload = None, handler = None):
    if user.hasAcces("lis","connector") is True:
        db = inventoryd.db(inventoryd.localData.cfg["db"])
        connectors = db.getConnectors(False)
        db.disconnect()
        handler.send_response(200)
        handler.send_header('Content-Type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps(connectors, sort_keys=True, indent=4, separators=(',',': ')))
        return True
    else:
        self.send_response(401)
        return True

def createConnector(user = None, payload = None, handler = None):
    if user.hasAcces("create","connector") is True:
        connector = RESTconnectorHandler(payload)
        res = connector.create()
        if res is True:
            handler.send_response(201)
            handler.send_header('Content-Type', 'application/json')
            handler.end_headers()
            handler.wfile.write(json.dumps({'rc':201,'message':'Connection created'}, sort_keys=True, indent=4, separators=(',',': ')))
        else:
            handler.send_response(400)
            handler.send_header('Content-Type', 'application/json')
            handler.end_headers()
            handler.wfile.write(json.dumps({'rc':400,'message':connector.err}, sort_keys=True, indent=4, separators=(',',': ')))
        return True
    else:
        self.send_response(401)
        return True

def getConnectorIdFromPath(path):
    res = re.search('(?<=connector/)[0-9]+',path)
    
    if res is not None:
        return int(res.group())
    else:
        return -1

def modifyConnector(user = None, payload = None, handler = None):
    payload["id"] = getConnectorIdFromPath(handler.path)
    if user.hasAcces("modify","connector") is True:
        connector = RESTconnectorHandler(payload)
        res = connector.modify()
        if res is True:
            handler.send_response(200)
            handler.send_header('Content-Type', 'application/json')
            handler.end_headers()
            handler.wfile.write(json.dumps({'rc':200,'message':'Connection modified'}, sort_keys=True, indent=4, separators=(',',': ')))
        else:
            handler.send_response(400)
            handler.send_header('Content-Type', 'application/json')
            handler.end_headers()
            handler.wfile.write(json.dumps({'rc':400,'message':connector.err}, sort_keys=True, indent=4, separators=(',',': ')))
        return True
    else:
        handler.send_response(401)
        return True

def deleteConnector(user = None, payload = None, handler = None):
    payload["id"] = getConnectorIdFromPath(handler.path)
    if user.hasAcces("delete","connector") is True:
        connector = RESTconnectorHandler(payload)
        res = connector.delete()
        if res is True:
            handler.send_response(200)
            handler.send_header('Content-Type', 'application/json')
            handler.end_headers()
            handler.wfile.write(json.dumps({'rc':200,'message':'Connection deleted'}, sort_keys=True, indent=4, separators=(',',': ')))
        else:
            handler.send_response(400)
            handler.send_header('Content-Type', 'application/json')
            handler.end_headers()
            handler.wfile.write(json.dumps({'rc':400,'message':connector.err}, sort_keys=True, indent=4, separators=(',',': ')))
        return True
    else:
        handler.send_response(401)
        return True

def readConnector(user = None, payload = None, handler = None):
    payload["id"] = getConnectorIdFromPath(handler.path)
    if user.hasAcces("read","connector") is True:
        connector = RESTconnectorHandler(payload)
        res = connector.read()
        if res is True:
            handler.send_response(200)
            handler.send_header('Content-Type', 'application/json')
            handler.end_headers()
            handler.wfile.write(json.dumps({'rc':200,'message':'Connection read','payload':connector.getData()}, sort_keys=True, indent=4, separators=(',',': ')))
        else:
            handler.send_response(400)
            handler.send_header('Content-Type', 'application/json')
            handler.end_headers()
            handler.wfile.write(json.dumps({'rc':400,'message':connector.err}, sort_keys=True, indent=4, separators=(',',': ')))
        return True
    else:
        handler.send_response(401)
        return True

def disableConnector(user = None, payload = None, handler = None):
    payload["id"] = getConnectorIdFromPath(handler.path)
    if user.hasAcces("modify","connector") is True:
        connector = RESTconnectorHandler(payload)
        res = connector.disable()
        if res is True:
            handler.send_response(200)
            handler.send_header('Content-Type', 'application/json')
            handler.end_headers()
            handler.wfile.write(json.dumps({'rc':200,'message':'Connection disabled'}, sort_keys=True, indent=4, separators=(',',': ')))
        else:
            handler.send_response(400)
            handler.send_header('Content-Type', 'application/json')
            handler.end_headers()
            handler.wfile.write(json.dumps({'rc':400,'message':connector.err}, sort_keys=True, indent=4, separators=(',',': ')))
        return True
    else:
        handler.send_response(401)
        return True


def enableConnector(user = None, payload = None, handler = None):
    payload["id"] = getConnectorIdFromPath(handler.path)
    if user.hasAcces("modify","connector") is True:
        connector = RESTconnectorHandler(payload)
        res = connector.enable()
        if res is True:
            handler.send_response(200)
            handler.send_header('Content-Type', 'application/json')
            handler.end_headers()
            handler.wfile.write(json.dumps({'rc':200,'message':'Connection enabled'}, sort_keys=True, indent=4, separators=(',',': ')))
        else:
            handler.send_response(400)
            handler.send_header('Content-Type', 'application/json')
            handler.end_headers()
            handler.wfile.write(json.dumps({'rc':400,'message':connector.err}, sort_keys=True, indent=4, separators=(',',': ')))
        return True
    else:
        handler.send_response(401)
        return True

def getHostnameFromPath(path):
    res = re.search('(?<=hostvars/)[a-zA-Z0-9\.-_]+(?=/.*)',path)
    
    if res is not None:
        return res.group()
    else:
        return None

def listHosts(user = None, payload = None, handler = None):
    if user.hasAcces("list","host") is True:
        db = inventoryd.db(inventoryd.localData.cfg["db"])
        hosts = db.getHosts()
        db.disconnect()
        handler.send_response(200)
        handler.send_header('Content-Type', 'application/json')
        handler.end_headers()
        handler.wfile.write(json.dumps(hosts, sort_keys=True, indent=4, separators=(',',': ')))
        return True
    else:
        handler.send_response(401)
        return True
    
def createHostvars(user = None, payload = None, handler = None):
    payload["id"] = getHostnameFromPath(handler.path)
    if user.hasAcces("create","host") is True:
        hostvars = RESThostvarsHandler(payload)
        res = hostvars.create()
        if res is True:
            handler.send_response(200)
            handler.send_header('Content-Type', 'application/json')
            handler.end_headers()
            handler.wfile.write(json.dumps({'rc':200,'message':'Hostvars created'}, sort_keys=True, indent=4, separators=(',',': ')))
        else:
            handler.send_response(400)
            handler.send_header('Content-Type', 'application/json')
            handler.end_headers()
            handler.wfile.write(json.dumps({'rc':400,'message':hostvars.err}, sort_keys=True, indent=4, separators=(',',': ')))
        return True
    else:
        handler.send_response(401)
        return True
    
def modifyHostvars(user = None, payload = None, handler = None):
    payload["id"] = getHostnameFromPath(handler.path)
    if user.hasAcces("modify","host") is True:
        hostvars = RESThostvarsHandler(payload)
        res = hostvars.modify()
        if res is True:
            handler.send_response(200)
            handler.send_header('Content-Type', 'application/json')
            handler.end_headers()
            handler.wfile.write(json.dumps({'rc':200,'message':'Hostvars modified'}, sort_keys=True, indent=4, separators=(',',': ')))
        else:
            handler.send_response(400)
            handler.send_header('Content-Type', 'application/json')
            handler.end_headers()
            handler.wfile.write(json.dumps({'rc':400,'message':hostvars.err}, sort_keys=True, indent=4, separators=(',',': ')))
        return True
    else:
        handler.send_response(401)
        return True
    
def deleteHostvars(user = None, payload = None, handler = None):
    payload["id"] = getHostnameFromPath(handler.path)
    if user.hasAcces("delete","host") is True:
        hostvars = RESThostvarsHandler(payload)
        res = hostvars.delete()
        if res is True:
            handler.send_response(200)
            handler.send_header('Content-Type', 'application/json')
            handler.end_headers()
            handler.wfile.write(json.dumps({'rc':200,'message':'Hostvars deleted'}, sort_keys=True, indent=4, separators=(',',': ')))
        else:
            handler.send_response(400)
            handler.send_header('Content-Type', 'application/json')
            handler.end_headers()
            handler.wfile.write(json.dumps({'rc':400,'message':hostvars.err}, sort_keys=True, indent=4, separators=(',',': ')))
        return True
    else:
        handler.send_response(401)
        return True
    
def readHostvars(user = None, payload = None, handler = None):
    payload["id"] = getHostnameFromPath(handler.path)
    if user.hasAcces("read","host") is True:
        host = RESThostvarsHandler(payload)
        res = host.read()
        if res is True:
            handler.send_response(200)
            handler.send_header('Content-Type', 'application/json')
            handler.end_headers()
            handler.wfile.write(json.dumps({'rc':200,'message':'Host read','payload':host.getData()}, sort_keys=True, indent=4, separators=(',',': ')))
        else:
            handler.send_response(400)
            handler.send_header('Content-Type', 'application/json')
            handler.end_headers()
            handler.wfile.write(json.dumps({'rc':400,'message':host.err}, sort_keys=True, indent=4, separators=(',',': ')))
        return True
    else:
        handler.send_response(401)
        return True
    
class RESTRequestHandler(BaseHTTPRequestHandler):
        
    def do_GET(self):
        inventoryd.logmessage(severity="debug", message="GET request (%s)." % self.path)

        urlHandler = { '/inventory': inventoryd.restserver.showInventory }
        
        for url in urlHandler:
            if re.match('^%s$' % url, self.path) is not None:
                return urlHandler[url]( handler=self)

        self.send_response(404)
        return None
    
    def do_POST(self):
        inventoryd.logmessage(severity="debug", message="POST request (%s)." % self.path)

        urlHandler = { '/inventory': inventoryd.restserver.showInventory,
                       '/admin/connector/list': inventoryd.restserver.listConnectors,
                       '/admin/connector/create': inventoryd.restserver.createConnector,
                       '/admin/connector/[0-9]+/modify': inventoryd.restserver.modifyConnector,
                       '/admin/connector/[0-9]+/delete': inventoryd.restserver.deleteConnector,
                       '/admin/connector/[0-9]+/show': inventoryd.restserver.readConnector,
                       '/admin/connector/[0-9]+/disable': inventoryd.restserver.disableConnector,
                       '/admin/connector/[0-9]+/enable': inventoryd.restserver.enableConnector,
                       '/admin/host/list': inventoryd.restserver.listHosts,
                       '/admin/hostvars/[a-zA-Z0-9\.-_]+/create': inventoryd.restserver.createHostvars,
                       '/admin/hostvars/[a-zA-Z0-9\.-_]+/modify': inventoryd.restserver.modifyHostvars,
                       '/admin/hostvars/[a-zA-Z0-9\.-_]+/delete': inventoryd.restserver.deleteHostvars,
                       '/admin/hostvars/[a-zA-Z0-9\.-_]+/show': inventoryd.restserver.readHostvars
                     }
                        
        content_len = int(self.headers.getheader('content-length', 0))
        post_data = self.rfile.read(content_len)
        try:
            json.loads(post_data)
        except:
            post_data = json.loads("{}")
        else:
            post_data = json.loads(post_data)
        
        try:
            post_data["username"]
        except:
            post_data["username"] = ""
        
        try:
            post_data["passphrase"]
        except:
            post_data["passphrase"] = None
            
        try:
            post_data["token"]
        except:
            post_data["token"] = None

        try:
            post_data["payload"]
        except:
            post_data["payload"] = {}
        
        user = inventoryd.user(post_data["username"])
        if post_data["passphrase"] is not None:
            user.authenticate(passphrase=post_data["passphrase"])
        elif post_data["token"] is not None:
            user.authenticate(token=post_data["token"])
        
        for url in urlHandler:
            if re.match('^%s$' % url, self.path) is not None:
                return urlHandler[url](user=user, payload=post_data["payload"], handler=self)

        self.send_response(404)
        return None

class RESTconnectorHandler():
    _id = -1
    _name = None
    _connector = None
    _type = None
    _typelist = [ 'hosts', 'groups' ]
    _parameters = None
    _priority = 0
    _data = dict()
    
    _err = list()
    
    def __init__(self, config = {}):
        try:
            config["id"]
        except:
            config["id"] = -1
        
        try:
            config["name"]
        except:
            config["name"] = None
        
        try:
            config["connector"]
        except:
            config["connector"] = None
        
        try:
            config["type"]
        except: 
            config["type"] = None
        
        try:
            config["parameters"]
        except:
            config["parameters"] = None
        
        try:
            config["priority"]
        except:
            config["priority"] = None
    
        self._id = config["id"]
        self._name = config["name"]
        self._connector = config["connector"]
        self._type = config["type"]
        self._parameters = config["parameters"]
        self._priority = config["priority"]
    
    def create(self):
        if self._name is None:
            self._err.append('You need to specify a connector name')
    
        if self._connector is None:
            self._err.append('You need to specify a connector')
    
        if self._type is None:
            self._err.append('You need to specify the connector type (%s)' % "|".join(self._typelist))
        elif isinstance(self._type, str) and self._type not in self._typelist:
            self._err.append('Connector type cannot be %s. It has to be one of these: %s.' % (self._type, ",".join(self._typelist)))
    
        if self._parameters is None:
            self._err.append('You need to specify the connector parameters')
    
        if self._parameters is None:
            self._err.append('You need to specify the connector priority')
        
        if len(self._err) > 0:
            return False
        
        db = inventoryd.db(inventoryd.localData.cfg["db"])
        res = db.createConnector(name = self._name, connector = self._connector, connector_type = self._type, parameters = self._parameters, priority = self._priority)
        db.disconnect()

        return res
        
    def modify(self):
        db = inventoryd.db(inventoryd.localData.cfg["db"])
        res = db.modifyConnector(id = self._id, name = self._name, connector = self._connector, type = self._type, parameters = json.dumps(self._parameters), priority = self._priority)
        db.disconnect()

        return res
    
    def delete(self, connector_id = -1):
        db = inventoryd.db(inventoryd.localData.cfg["db"])
        res = db.deleteConnector(connector_id = self._id)
        db.disconnect()
        return res
        
    def read(self, connector_id = -1):
        if connector_id > 0:
            self._id = connector_id
        self._data = dict()
        db = inventoryd.db(inventoryd.localData.cfg["db"])
        res = db.readConnector(connector_id = self._id)
        try:
            res["id"]
        except:
            res["id"] = -1
        
        try:
            res["name"]
        except:
            res["name"] = None
        
        try:
            res["connector"]
        except:
            res["connector"] = None
        
        try:
            res["enabled"]
        except:
            res["enabled"] = False
        
        try:
            res["priority"]
        except:
            res["priority"] = 0
        
        try:
            res["type"]
        except:
            res["type"] = None
        
        try:
            res["parameters"]
        except:
            res["parameters"] = None
        
        self._id = res["id"]
        self._name = res["name"]
        self._connector = res["connector"]
        self._enabled = res["enabled"]
        self._priority = res["priority"]
        self._type = res["type"]
        self._parameters = res["parameters"]
        
        db.disconnect()
        return True
    
    def getData(self):
        return { 'id': self._id, 'name': self._name, 'connector': self._connector, 'enabled': self._enabled, 'priority': self._priority, 'type': self._type, 'parameters': self._parameters }
        
    def enable(self, connector_id = -1):
        if connector_id > 0:
            self._id = connector_id
        db = inventoryd.db(inventoryd.localData.cfg["db"])
        res = db.enableConnector(connector_id = self._id)
        db.disconnect()
        return True

    def disable(self, connector_id = -1):
        if connector_id > 0:
            self._id = connector_id
        db = inventoryd.db(inventoryd.localData.cfg["db"])
        res = db.disableConnector(connector_id = self._id)
        db.disconnect()
        return True

class RESThostvarsHandler():
    _id = None
    _hostname = None
    _vars = list()
    
    def __init__(self, config = {}):
        try:
            config["id"]
        except:
            config["id"] = None
        
        try:
            config["vars"]
        except:
            config["vars"] = list()
        
        self._id = config["id"]
        self._hostname = config["id"]
        self._vars = config["vars"]
    
    def create(self):
        db = inventoryd.db(inventoryd.localData.cfg["db"])
        for el in self._vars:
            res = db.createStaticHostvar(hostname = self._hostname, fact = el["fact"], value = el["value"], priority = el["priority"])
                
        db.disconnect()
        return True

    def delete(self):
        db = inventoryd.db(inventoryd.localData.cfg["db"])
        for el in self._vars:
            res = db.deleteStaticHostvar(hostname = self._hostname, fact = el["fact"])
                
        db.disconnect()
        return True
        
    def disable(self):
        return True
        
    def enable(self):
        return True
        
    def getData(self):
        return self._vars
        
    def modify(self):
        db = inventoryd.db(inventoryd.localData.cfg["db"])
        for el in self._vars:
            res = db.modifyStaticHostvar(hostname = self._hostname, fact = el["fact"], value = el["value"], priority = el["priority"])
                
        db.disconnect()
        return True

    def read(self, host_id = None):
        if host_id is not None:
            self._id = host_id
        self._data = dict()
        
        db = inventoryd.db(inventoryd.localData.cfg["db"])
        self._vars = db.readHost(host_id = self._id)
        db.disconnect()
        return True
        
        
class ThreadedRESTserver(ThreadingMixIn, HTTPServer):
    allow_reuse_address = True
    
    def shutdown(self):
        self.socket.close()
        HTTPServer.shutdown(self)

class RESTserver():
    _ip = ""
    _port = -1
    _certificate_path = None
    
    def __init__(self, ip, port = -1, certificate_path = None, keyfile_path = None):
        self._ip = ip
        self._port = port
        self._certificate_path = certificate_path
        self._keyfile_path = keyfile_path
        
        inventoryd.logmessage(severity="debug", message="Creating REST server.")
        inventoryd.logmessage(severity="debug", message="REST server address: %s " % ip)
        inventoryd.logmessage(severity="debug", message="REST server port: %d " % port)
        if certificate_path is not None and keyfile_path is not None:
            inventoryd.logmessage(severity="debug", message="REST server certificate: %s " % certificate_path)
            inventoryd.logmessage(severity="debug", message="REST server keyfile: %s " % keyfile_path)
        
        if self._port != -1:
            self.server = ThreadedRESTserver((ip,port), RESTRequestHandler)
            if certificate_path is not None and keyfile_path is not None:
                self.server.socket = ssl.wrap_socket(self.server.socket, server_side=True, certfile=certificate_path, keyfile=keyfile_path)
            
        return None
        
    def start(self):
        if self._port != -1:
            inventoryd.logmessage(severity="debug", message="Starting REST server (%s:%d)." % (self._ip, self._port))
            self.server_thread = threading.Thread(target=self.server.serve_forever)
            self.server_thread.start()
            inventoryd.logmessage(severity="debug", message="REST server (%s:%d) started." % (self._ip, self._port))
        return True
    
    def waitForThread(self):
        if self._port != -1:
            self.server_thread.join(None)
        return True
    
    def stop(self):
        if self._port != -1:
            inventoryd.logmessage(severity="debug", message="Stopping REST server (%s:%d)." % (self._ip, self._port))
            self.server.shutdown()
            self.waitForThread()
            inventoryd.logmessage(severity="debug", message="REST server (%s:%d) Stopped." % (self._ip, self._port))
        return True
