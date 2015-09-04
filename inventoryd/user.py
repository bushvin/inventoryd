import inventoryd
import hashlib

class user():
    _username = None
    _new = True
    _token = None
    _roles = []
    _acl= None
    _authenticated = False
    
    def __init__(self, username = None):
        if username is not None:
            self._username = username
            self._getUserInfo()
        
    def _getUserInfo(self):
        db = inventoryd.db(inventoryd.localData.cfg["db"])
        userinfo = db.getUserInfo(self._username)
        db.disconnect()
        if userinfo is not None:
            self._name = userinfo["name"]
            self._new = False
    
    def _getRoles(self):
        db = inventoryd.db(inventoryd.localData.cfg["db"])
        roles = db.getRoles(self._username)
        db.disconnect()
        self._roles = []
        for el in roles:
            self._roles.append(inventoryd.role(el["name"]))
        
        
    def authenticate(self, passphrase = None, token = None, username = None):
        if username is not None:
            self._username = username
        if token is not None:
            self._token = token
            auth_type='token'
            
        if passphrase is not None:
            auth_type='passphrase'
        
        if auth_type == 'passphrase':
            db = inventoryd.db(inventoryd.localData.cfg["db"])
            db_salt, db_pass = db.getUserPassword(self._username)
            db.disconnect()
            hashpass = hashlib.sha512('%s:%s' % (db_salt,passphrase)).hexdigest()
            if hashpass == db_pass:
                self._authenticated = True
            else:
                self._authenticated = False
        
        return self._authenticated
    
    def isAuthenticated(self):
        return self._authenticated
    
    def hasAcces(self, ace, objectname):
        self.getUserACL()
        return self._acl.getACE(ace, objectname)
        
    def getUserACL(self):
        if self._acl is None:
            db = inventoryd.db(inventoryd.localData.cfg["db"])
            self._acl = inventoryd.acl(db.getUserACL(self._username))
            #self._acl = db.getUserACL(self._username)
        
        #print self._acl
        return self._acl
        
        
            
            
"""
class role():
    _role_name = None
    _new = True
    _members = []
    _acl = None
    
    def __init__(self, role_name = None):
        if rolename is not None:
            self._role_name = role_name

    def _getRoleInfo(self):
        db = inventoryd.db(inventoryd.localData.cfg["db"])
        roleinfo = db.getRoleInfo(self._role_name)
        db.disconnect()
        if roleinfo is not None:
            self._name = roleinfo["name"]
            self._new = False
    
    def _getMembers(self):
        db = inventoryd.db(inventoryd.localData.cfg["db"])
        self._members = db.getRoleMembers(self._role_name)
        db.disconnect()
    
    def _getACL(self):
        db = inventoryd.db(inventoryd.localData.cfg["db"])
        acl = db.getRoleACL(self._role_name)
        db.disconnect()
        self._acl = inventoryd.acl(acl)
"""

class acl():
    _acl = []
    _acelist = [ 'list', 'read','create', 'delete', 'modify' ]
    def __init__(self, acl = None):
        if isinstance(acl, list) is True:
            self._acl = acl
        return None

    def getACE(self, ace, object):
        if ace.lower() not in self._acelist:
            return False
        
        res = False
        for el in self._acl:
            try:
                el["ace_%s" % ace]
            except:
                el["ace_%s" % ace] = 0
                
            if el["ace_%s" % ace] == 1:
                res = True
        return res
