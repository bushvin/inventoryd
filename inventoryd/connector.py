import sys
import json
import csv
from io import BytesIO
import inventoryd
import datetime
import copy

class connector(object):
    _hosts = dict()
    _hostlist = list()
    _groups = dict()
    _parameters = dict()
    _schema = dict()
    _args = [ {'name':'prefix', 'mandatory':False, 'default':'' },
              {'name':'schema', 'mandatory':True, 'default':None } ]
    _defaultItemSchema = { 'datatype':'string', 'index':-1, 'name':'', 'default': '' }
    connector_name = ''
    rc = 0
    message = ""
    
    def __init__(self, parameters=dict(), args=list()):
        self._setParameters(parameters)
        self._args = self._args + args

    def _setParameters(self, parameters = dict()):
        self._parameters = parameters
        self._schema = self.getParameter("schema")
    
    def getHostCount(self):
        hosts = list(set(copy.copy(self._hostlist)))
        return len(hosts)
    
    def getSchemaItem(self, item, item_property = None):
        for el in self._schema:
            if el["name"] == item:
                if item_property is None:
                    return el
                else:
                    try:
                        el[item_property]
                    except:
                        return None
                    else:
                        return el[item_property]
        return None
    
    def applySchema(self, item, value):
        
        itemschema = self.getSchemaItem(item)
        if self.getSchemaItem(item) is None:
            return value
        itemschema = copy.copy(self._defaultItemSchema)
        itemschema.update(self.getSchemaItem(item))
        
        
        
        if itemschema["datatype"] == 'int' or itemschema["datatype"] == 'integer':
            try:
                int(value)
            except:
                value = itemschema["default"]
            else:
                value = int(value)
        elif itemschema["datatype"] == 'str' or itemschema["datatype"] == 'string':
            try:
                str(value)
            except:
                value = itemschema["default"]
            else:
                value = str(value)
        elif itemschema["datatype"] == 'bool' or itemschema["datatype"] == 'boolean':
            try:
                bool(value)
            except:
                value = itemschema["default"]
            else:
                value = bool(value)
            
        return value
    
    def getSchemaFactName(self, fact_index):
        for el in self._schema:
            if el["index"] == fact_index:
                return el["name"]
        return fact_index
        
    def updateArguments(self, arglist = list()):
        newargs = list()
        for arg in (self._args + arglist):
            try:
                arg["name"]
            except:
                inventoryd.logmessage(severity="crit", message="argument name is missing.")
                #print "argument name missing!"
                sys.exit(1)
            
            try:
                arg["mandatory"]
            except:
                arg["mandatory"] = False
            
            try:
                arg["default"]
            except:
                arg["default"] = None
            
            newargs.append(arg)
            self._args = newargs

    def checkParameters(self):
        for arg in self._args:
            if arg["mandatory"] is True:
                try:
                    self._parameters[arg["name"]]
                except:
                    #print "%s is a mandatory argument for the %s connector." % ( arg["name"], self.connector_name )
                    inventoryd.logmessage(severity="crit", message="%s is a mandatory argument for the %s connector." % ( arg["name"], self.connector_name))
                    sys.exit(1)
        
        return True

    def getParameter(self, parametername):
        argfound = False
        for arg in self._args:
            if arg["name"] == parametername:
                defaultval = arg["default"]
                argfound = True
                break
        if argfound is False:
            #print "The requested parameter (%s) is not known to the %s connector." % ( parametername, self.connector_name )
            inventoryd.logmessage(severity="crit", message="The requested parameter (%s) is not known to the %s connector." % ( parametername, self.connector_name))
            sys.exit(1)
        
        try:
            self._parameters[parametername]
        except:
            return defaultval
        else:
            return self._parameters[parametername]
            
    def getHosts(self):
        self.checkParameters()
        return "getHosts"
    
    def getGroups(self):
        self.checkParameters()
        return "getGroups"
    
    def showHelp(self):
        return "showHelp"
    
    def showConnectionParameters(self):
        return "showConnectionParameters"
    
    def addPrefixToList(self, varslist):
        if self.getParameter("prefix") == "":
            return True
        pfx = self.getParameter("prefix")
        
        if varslist == "hostvars":
            for host in self._hosts:
                for fact in self._hosts[host]:
                    newfact = self.addPrefixToFact(fact, pfx)
                    val = self._hosts[host][fact]
                    del self._hosts[host][fact]
                    self._hosts[host][newfact] = val
        elif varslist == "groupvars":
            for group in self._groups:
                for fact in self._groups[group]["vars"]:
                    newfact = self.addPrefixToFact(fact, pfx)
                    val = self._groups[group]["vars"][fact]
                    del self._groups[group]["vars"][fact]
                    self._groups[group]["vars"][newfact] = val
        else:
            return False
        return True
    
    def addPrefixToFact(self, fact, prefix):
        if fact[0:len(fact)] != prefix:
            fact = prefix + fact
        
        return fact
    
    def convertJSONHosts(self, json_string = "[]"):
        facts = list()
        data = json.loads(json_string)
        hostname_index = self.getSchemaItem("hostname", "index")
        
        for row in data:
            facts = facts + [ { 'hostname':row[hostname_index], 'fact':self.getSchemaFactName(fact), 'value':self.applySchema(fact,row[fact]) } for fact in row ]
            self._hostlist.append(row[hostname_index])
        
        return facts
    
    def convertJSONGroups(self, json_string = "{}"):
        facts = list()
        hosts = list()
        children = list()
        
        data = json.loads(json_string)
        groupname_index = self.getSchemaItem("groupname", "index")
        hostname_index = self.getSchemaItem("hostname", "index")
        parent_index = self.getSchemaItem("parent", "index")
        
        for row in data:
            for el in row:
                if el not in (groupname_index, hostname_index, parent_index):
                    facts.append( { 'groupname':row[groupname_index], 'fact':self.getSchemaFactName(el), 'value':self.applySchema(el,row[el]) } )
                elif el == hostname_index:
                    hosts.append( { 'groupname':row[groupname_index], 'host':row[el] } )
                elif el == parent_index:
                    children.append( { 'groupname':row[el], 'child':row[groupname_index] } )
        
        
        return facts, hosts, children

    def convertCSVHosts(self, csv_data = ""):
        facts = list()
        hostname_index = str(self.getSchemaItem("hostname", "index"))
        
        fields = list()
        for el in sorted(self.getParameter("schema"), key=lambda k: k["index"]):
            el["index"] = str(el["index"])
            fields.append(el["index"])
        
        f = BytesIO(csv_data)
        rdr = csv.reader(f, delimiter=self.getParameter('delimiter'), quotechar=self.getParameter('quotechar'))
        for row in rdr:
            row = dict(zip(fields,row))
            
            facts = facts + [ { 'hostname':row[hostname_index], 'fact':self.getSchemaFactName(fact), 'value':self.applySchema(fact,row[fact]) } for fact in row ]
            self._hostlist.append(row[hostname_index])
            
        return facts

    def convertCSVGroups(self, csv_data = ""):
        facts = list()
        hosts = list()
        children = list()
        groupname_index = self.getSchemaItem("groupname", "index")
        hostname_index = self.getSchemaItem("hostname", "index")
        parent_index = self.getSchemaItem("parent", "index")

        fields = list()
        for el in sorted(self.getParameter("schema"), key=lambda k: k["index"]):
            el["index"] = str(el["index"])
            fields.append(el["index"])
        
        f = BytesIO(csv_data)
        rdr = csv.reader(f, delimiter=self.getParameter('delimiter'), quotechar=self.getParameter('quotechar'))
        for row in rdr:
            row = dict(zip(fields,row))

            for el in row:
                if el not in (groupname_index, hostname_index, parent_index):
                    facts.append( { 'groupname':row[groupname_index], 'fact':self.getSchemaFactName(el), 'value':self.applySchema(el,row[el]) } )
                elif el == hostname_index:
                    hosts.append( { 'groupname':row[groupname_index], 'host':row[el] } )
                elif el == parent_index:
                    children.append( { 'groupname':row[el], 'child':row[groupname_index] } )

        return facts, hosts, children

    def csvLineToList(self, value):
        reader = csv.reader(BytesIO(value), delimiter=self.getParameter('delimiter'), quotechar=self.getParameter('quotechar'))
        res = []
        for row in reader:
            res = list(row)
            break


        return res
