import inventoryd
from urlparse import urlparse
import pycurl
import os
from StringIO import StringIO as BytesIO

class connector_uri(inventoryd.connector):
    
    connector_name = 'uri'

    def getHosts(self):
        args = [ { 'name': 'uri', 'mandatory':True, 'default':None },
                 { 'name': 'format', 'mandatory':False, 'default': 'json' },
                 { 'name': 'insecure', 'mandatory': False, 'default': False },
                 { 'name': 'delimiter', 'mandatory': False, 'default': ',' },
                 { 'name': 'quotechar', 'mandatory': False, 'default': '"' },
                 { 'name': 'header', 'mandatory': False, 'default': None } ]
        if self.updateArguments(args) is False:
            return list()
            
        super(connector_uri,self).getHosts()
        
        if self.rc != 0:
            return list()
            
        data = self.getFileContents()
        if data is None:
            self._hosts = dict()
        elif self.getParameter("format") == "json":
            self._hosts = self.convertJSONHosts(data)
        elif self.getParameter("format") == "csv":
            self._hosts = self.convertCSVHosts(data)
            
        self.addPrefixToList("hostvars")
        return self._hosts
    
    def getGroups(self):
        args = [ { 'name':'uri', 'mandatory':True, 'default':None },
                 { 'name':'format', 'mandatory':False, 'default': 'json' },
                 { 'name':'insecure', 'mandatory': False, 'default': False } ]
        if self.updateArguments(args) is False:
            return list()
            
        super(connector_uri,self).getGroups()

        if self.rc != 0:
            return list()

        data = self.getFileContents()
        if data is None:
            self._groups = dict()
        elif self.getParameter("format") == "json":
            self._groups = self.convertJSONGroups(data)
        elif self.getParameter("format") == "csv":
            self._groups = self.convertCSVGroups(data)
            
        return self._groups
    
    def showHelp(self):
        parent = super(connector_uri,self).showHelp()
        return "showHelp"
    
    def showConnectionParameters(self):
        parent = super(connector_uri,self).showConnectionParameters()
        return "showConnectionParameters"

    def getFileContents(self):
        res = urlparse(self.getParameter("uri"))
        if (res.scheme == "" and res.netloc == "") or res.scheme == "file":
            data = self.getLocalFileContents(res.path)
        
        elif (res.scheme == "" and res.netloc != "") or res.scheme == "http" or res.scheme == "https":
            data = self.getHTTPfileContents(self.getURL(res))
        
        return data

    def getLocalFileContents(self, path):
        if os.path.isfile(path):
            with open(path,'r') as f:
                data = f.read()
        else:
            message = "%s connector error: The path specified (%s) is invalid." % (self._connector_name, path)
            self.message = message
            self.rc = 1
            inventoryd.logmessage(severity="err", message=message)
            data = None
        return data

    def getHTTPfileContents(self, url):
        buffer = BytesIO()
        url = url.encode("utf8")
        con = pycurl.Curl()
        con.setopt(pycurl.URL, url)
        con.setopt(pycurl.WRITEFUNCTION, buffer.write)
        if self.getParameter("insecure") is True:
            con.setopt(pycurl.SSL_VERIFYPEER, 0)
            con.setopt(pycurl.SSL_VERIFYHOST, 0)
        else:
            con.setopt(pycurl.SSL_VERIFYPEER, 1)
            con.setopt(pycurl.SSL_VERIFYHOST, 2)
            
        con.perform()
        rc = con.getinfo(con.RESPONSE_CODE)
        con.close()
        if rc == 200:
            data = buffer.getvalue()
        else:
            message="%s connector error: There was an error retrieving data from %s. RC: %s" % (self.connector_name, url, rc)
            self.message = message
            self.rc = 1
            inventoryd.logmessage(severity="err", message=message)
            data = None
        return data

    def getURL(self, res):
        url = ""
        if res.scheme != "":
            url = url + res.scheme + "://"
        if res.netloc != "":
            url = url + res.netloc
        if res.path != "":
            url = url + res.path
        if res.query != "":
            url = url + "?" + res.query
        return url
