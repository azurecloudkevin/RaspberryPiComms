import json
import time, calendar

from numpy import true_divide
class queuedata:
    def __init__(self, hostID, hostIP):
        self.hostid = hostID
        self.ip = hostIP

    def create_heartbeat(self, alarmid, resolvedid):
        data= {"alarmID": alarmid, "host": self.hostid, "resolved": resolvedid}
        return data

    def isunresolved(self, data):
        returndata = self.resolvedstatus(data)
        if(returndata == 0):
            return True
        else:
            return False
    
    def resolvedstatus(self, data):
        returndata = json.load(data)
        resolution = returndata["resolved"]
        return resolution      

    def parse_data(self, jsonData):
        d = eval(jsonData)
        alarmid = d['alarmID']
        hostid = d['host']
        resolvedstatus = d['resolved']
        return (alarmid, hostid, resolvedstatus)
