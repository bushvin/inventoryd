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

from optparse import OptionParser
#from optparse import OptionGroup

def getcliargs():
    parser = OptionParser()
    
    parser.add_option("-C", "--config", help="Path to the config file", dest="configpath", action="store", type="string", default=None)
    parser.add_option("-P", "--pidfile", help="Path to the pid file", dest="pidfilepath", action="store", type="string", default="/var/run/inventoryd.pid")
    parser.add_option("-R", "--vardir", help="Path where inventoryd stores cache files", dest="varfilepath", action="store", type="string", default="/var/lib/inventoryd")
    
    (options, args) = parser.parse_args()
    
    return options
