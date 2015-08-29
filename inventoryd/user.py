import inventoryd

class user():
    _username = None
    _new = True
    _token = None
    _roles = []
    
    def __init__(self, username = None):
        if self._username is not None:
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
        
        
    def authenticate(self, password = None, token = None, username = None):
        if username is not None:
            self._username = username
            

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
            
class acl():
    _acl = []
    def __init__(self, acl = None):
        if isinstance(acl, list) is True:
            self._acl = acl
        return None
