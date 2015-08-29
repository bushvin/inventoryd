from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer
from SocketServer import ThreadingMixIn
import threading
import re
import inventoryd
import json
import ssl


class RESTRequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        inventoryd.logmessage(severity="debug", message="POST request (%s)." % self.path)
        inventoryd.logmessage(severity="alert", message="POST requests have not been implemented yet.")
        self.send_response(404)
        
    def do_GET(self):
        inventoryd.logmessage(severity="debug", message="GET request (%s)." % self.path)
        parameters = self.path.split("/")
        parameters.pop(0)
        if parameters[0] == "inventory":
            if len(parameters) < 2 or parameters[1] == "list":
                inventoryd.logmessage(severity="debug", message="Inventory pull request")
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                inventory = inventoryd.inventory()
                self.wfile.write(json.dumps(inventory.getOBJ(), sort_keys=True, indent=4, separators=(',',': ')))
                return True

        elif parameters[0] == "admin":
            if parameters[1] == "connector":
                if len(parameters) < 3 or parameters[2] == "list":
                    db = inventoryd.db(inventoryd.localData.cfg["db"])
                    connectors = db.getConnectors(False)
                    db.disconnect()
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(connectors, sort_keys=True, indent=4, separators=(',',': ')))
                    return True
            if parameters[1] == "user":
                if len(parameters) < 3 or parameters[2] == "list":
                    db = inventoryd.db(inventoryd.localData.cfg["db"])
                    connectors = db.getUsers(False)
                    db.disconnect()
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(connectors, sort_keys=True, indent=4, separators=(',',': ')))
                    return True
                    
        self.send_response(404)
        

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
        #else:
            
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
