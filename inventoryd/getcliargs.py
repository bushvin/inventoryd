from optparse import OptionParser
#from optparse import OptionGroup

def getcliargs():
    parser = OptionParser()
    
    parser.add_option("-C", "--config", help="Path to the config file", dest="configpath", action="store", type="string", default=None)
    parser.add_option("-P", "--pidfile", help="Path to the pid file", dest="pidfilepath", action="store", type="string", default="/var/run/inventoryd.pid")
    
    (options, args) = parser.parse_args()
    
    return options
