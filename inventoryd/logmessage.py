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

import inventoryd
import syslog
import time
import datetime

class logmessage():
    _facility = ""
    _severity = ""
    _message = ""
    _syslog_severity = [ "emerg", "alert", "crit", "err", "warning", "notice", "info", "debug" ]
    _syslog_facility = [ "kern", "user", "mail", "daemon", "auth", "syslog", "lpr", "news", "uucp", "authpriv", "ftp", "cron", "local0", "local1", "local2", "local3", "local4", "local5", "local6", "local7" ]

    def __init__(self, facility = "local0", severity = "err", message = None):
        self._facility = facility.lower()
        self._severity = severity.lower()
        self._message = message
        
        if self._facility not in self._syslog_facility:
            self._facility = inventoryd.localData.cfg["inventoryd"]["log_facility"]

        if self._severity not in self._syslog_severity:
            self._severity = "info"

        continue_log = False
        for el in self._syslog_severity:
            if el == self._severity:
                continue_log = True
            if el == inventoryd.localData.cfg["inventoryd"]["log_level"]:
                break
        if continue_log is True:
            self.logToSyslog()
            if inventoryd.localData.cli.daemonize is False:
                self.logToConsole()
    
    def logToSyslog(self):
        exec "facility = syslog.LOG_%s" % self._facility.upper()
        exec "severity = syslog.LOG_%s" % self._severity.upper()

        syslog.openlog('syslog',syslog.LOG_PID,facility)
        syslog.syslog(severity, "%s" % self._message)
        syslog.closelog()
        return True
    
    def logToConsole(self):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        length = 0
        for el in self._syslog_severity:
            if len(el) > length:
                length = len(el)
                
        print "%s - [ %s ] - %s" % (timestamp, self._severity.upper().ljust(length) , self._message)
