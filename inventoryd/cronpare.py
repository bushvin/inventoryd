import inventoryd
import datetime
import re
import math

class cronpare():
    _min = "*"
    _hour = "*"
    _dom = "*"
    _month = "*"
    _dow = "*"
    
    def __init__(self):
        return None
        
    def compare(self,cron_expr, date_comp = None):

        if cron_expr.lower() == "@yearly" or cron_expr.lower() == "@annually":
           cron_expr = "0 0 1 1 *"
        elif cron_expr.lower() == "@monthly":
            cron_expr = "0 0 1 * *"
        elif cron_expr.lower() == "@weekly":
            cron_expr = "0 0 * * 0"
        elif cron_expr.lower() == "@daily":
            cron_expr = "0 0 * * *"
        elif cron_expr.lower() == "@hourly":
            cron_expr = "0 * * * *"
        
        if len(cron_expr.split()) != 5:
            return False
        
        if date_comp is None:
            date_comp = datetime.datetime.today()

        (self._min, self._hour, self._dom, self._month, self._dow) = cron_expr.split()
        
        if self._in_min(date_comp.minute) and self._in_hour(date_comp.hour) and self._in_dom(date_comp.day) and self._in_month(date_comp.month) and self._in_dow(date_comp.weekday()):
            return True
        else:
            return False
    
    def _generateTimeRange(self, expr, minimum, maximum ):
        timelist = list()
        for el in expr.split(","):
            el = el.strip()
            if el == "*":
                for i in range(minimum, maximum + 1):
                    timelist.append(i)
            elif re.match("^\*/[0-9]+$", el) is not None:
                fraction = int(el[2:])
                for i in range(minimum, maximum + 1, fraction):
                    timelist.append(i)
            elif re.match("^[0-9]+$", el) is not None:
                if int(el) >= minimum and int(el) <= maximum:
                    timelist.append(int(el))
            elif re.match("^[0-9]+-[0-9]+$", el):
                el_list = [int(i) for i in el.split("-") ]
                
                if el_list[0] < el_list[1] and el_list[0] >= minimum and el_list[1] <= maximum:
                    for i in range(int(el_list[0]),int(el_list[1])):
                        minutes.append(i)
        return timelist
    
    def _in_min( self, minute ):
        if minute in self._generateTimeRange(self._min, 0, 59):
            return True
        else:
            return False
    
    def _in_hour( self, hour ):
        if hour in self._generateTimeRange(self._hour, 0, 59):
            return True
        else:
            return False
    
    def _in_dom( self, dom ):
        if dom in self._generateTimeRange(self._dom, 1,31):
            return True
        else:
            return False
    
    def _in_month( self, month ):
        if month in self._generateTimeRange(self._month, 1, 12):
            return True
        else:
            return False
    
    def _in_dow( self, dow ):
        short_dow = [ 'sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat' ]
        long_dow = [ 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday' ]
        new_dow = list()
        for el in self._dow.split(','):
            el = el.strip().lower()
            resolved = False
            try:
                short_dow.index(el)
            except:
                el = el
            else:
                new_dow.append(short_dow.index(el))
                continue
            
            try:
                long_dow.index(el)
            except:
                el = el
            else:
                new_dow.append(long_dow.index(el))
                continue
            
            new_dow.append(el)
        
        self._dow = ",".join(new_dow)
        if dow in self._generateTimeRange(self._dow, 0, 7):
            return True
        else:
            return False
    
    
            # 0-1,*/5,8,17 => 0,1,5,8,10,15,17,20,25,30,35,40,45,50,55
                
                
        
