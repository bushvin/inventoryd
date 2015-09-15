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
from cronpare import cronpare
import copy
import re

class localData(object):
    cfg = {}
    cli = {}
