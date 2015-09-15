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

import sys

if sys.version_info < (2, 6):
    raise RuntimeError('You need Python 2.6+ for this module.')


__author__ = "William Leemans <willie@elaba.net>"
__license__ = "GNU Lesser General Public License (LGPL)"

from inventoryd.user import user 
from inventoryd.user import acl
from inventoryd.restserver import RESTserver
from inventoryd.getconfig import getconfig
from inventoryd.getcliargs import getcliargs
from inventoryd.db import db
from inventoryd.db_sqlite3 import db_sqlite3
from inventoryd.connector import connector
from inventoryd.connector_uri import connector_uri
from inventoryd.logmessage import logmessage
from inventoryd.daemon import daemon
from inventoryd.cronpare import cronpare

from jinja2 import Template

import copy
import re

__all__ = [ 'user',
            'acl',
            'RESTserver',
            'getconfig',
            'getcliargs',
            'db',
            'db_sqlite3',
            'connector',
            'connector_uri',
            'logmessage',
            'daemon',
            'cronpare' ]

class localData(object):
    cfg = {}
    cli = {}
