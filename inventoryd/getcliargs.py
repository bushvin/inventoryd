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
import os

def getcliargs():
    parser = OptionParser()
    
    parser.add_option("-C", "--config", help="Path to the config file", dest="configpath", action="store", type="string", default=None)
    parser.add_option("-P", "--pidfile", help="Path to the pid file", dest="pidfilepath", action="store", type="string", default="/var/run/inventoryd.pid")
    parser.add_option("-R", "--cachedir", help="Path where inventoryd stores cache files", dest="cachefilepath", action="store", type="string", default="/var/cache/inventoryd")
    
    (options, args) = parser.parse_args()
    
    if options.configpath is not None and os.path.isfile(options.configpath) is True:
        options.configpath = os.path.abspath(options.configpath)
    
    if os.path.isdir(os.path.dirname(options.pidfilepath)) is True:
        options.pidfilepath = os.path.abspath(options.pidfilepath)
    
    if os.path.isdir(options.cachefilepath) is True:
        options.cachefilepath = os.path.abspath(options.cachefilepath)
    return options
