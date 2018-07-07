"""views.utils
    Some utility functions
"""

from flask import g
#from app import app
from datetime import datetime, timedelta
import linecache
import sys
import re
    
def nowString():
    """Return the timestamp string in the normal format"""
    return datetime.now().isoformat()[:19]
    
def getDatetimeFromString(dateString):
    if type(dateString) is str: # or type(dateString) is unicode:
        pass
    else:
        return None
        
    dateString = dateString[:19]
    timeDelimiter = " "
    if "T" in dateString:
        timeDelimiter = "T"

    formatString = '%Y-%m-%d'+timeDelimiter+'%H:%M:%S'
    try:
        theDate = datetime.strptime(dateString, formatString) ## convert string to datetime
    except Exception as e:
        printException("Bad Date String","error",e)
        theDate = None
        
    if theDate == None:
        return None
        
    return theDate.replace(microsecond=0)


def getLocalTimeAtEvent(tz,isDST=0):
    """
        Return the current local time at an event location
    """
    localTime = datetime.utcnow() + timedelta(hours=(getTimeZoneOffset(tz))) ## get local time at the event location
    if(isDST == 1):
        localTime = localTime + timedelta(hours=1)
    
    return localTime.replace(microsecond=0)
    
def getTimeZones():
    # return a dictionary of time zone names and offsets
    tz = {"EST":{"longName" : 'New York US', "offset": -5}, 
          "CST":{"longName" : 'Chicago US', "offset": -6},
          "MST":{"longName" : 'Denver US', "offset": -7},
          "PST":{"longName" : 'Los Angeles US', "offset": -8},
         }
    return tz
    
def getTimeZoneOffset(zone=""):
    tz = getTimeZones()
    try:
        return tz[zone.upper()]["offset"]
    except KeyError:
        return 0
    
def printException(mes="An Unknown Error Occured",level="error",err=None):
    from app import app
    exc_type, exc_obj, tb = sys.exc_info()
    debugMes = None
    if tb is not None:
        f = tb.tb_frame
        lineno = tb.tb_lineno
        filename = f.f_code.co_filename
        linecache.checkcache(filename)
        line = linecache.getline(filename, lineno, f.f_globals)
        try:
            debugMes = 'EXCEPTION IN ({}, LINE {} "{}"): {}'.format(filename, lineno, line.strip(), exc_obj)
        except ValueError:
            debugMes = "Could not get error location info."
            
    if level=="error" or app.config["DEBUG"]:
        #always log errors
        if debugMes:
            app.logger.error(nowString() + " - " + debugMes)
        app.logger.error(nowString() + "   " + mes)
        if err:
            app.logger.error(nowString() + "    " + str(err))
        
    if app.config["DEBUG"]:
        if debugMes:
            mes = mes + " -- " +debugMes
        return mes
    else:
        return mes

def cleanRecordID(id):
    """ return the integer version of id or else -1 """
    if id is None:
        return -1
    if type(id) is str: # or type(id) is unicode:
        if id.isdigit():
            # a minus number like "-1" will fail this test, which is what we want
            return int(id)
        else:
            return -1
            
    #already a number 
    return id
    
def looksLikeEmailAddress(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email.strip())
    
