# importing socket module
from ast import And
from pydoc import resolve
from signal import alarm
import socket
import subprocess
import json
import os
from xmlrpc.client import DateTime
import modules.mysqlconnector as db
import modules.raspberrypi as pi
import modules.stringdata as qdata
import modules.socketcomms as sock
import uuid
import calendar
import time
import functools
from queue import Queue
import threading
import sys
import logging

PORT = 11000 #port for socket communication
DEBOUNCE_TIME = 5 #minimum seconds between button pushes
LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)

# logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)


## getting hostname by socket.gethostname method
hostname = socket.gethostname()

## getting ip address using socket.gethostbyname method

##  ip_address = socket.gethostbyname(hostname)
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect(("8.8.8.8", 80))
ip_address = s.getsockname()[0]          
print(f"Hostname: {hostname}")
print(f"IP Address: {ip_address}")
print (f"MAC Address: {hex(uuid.getnode())}")

hostID = uuid.getnode() & 0x00000000FFFF
print(f"Host ID from MAC is {hostID}")

file = open("config.json", "r")
data = json.load(file)
file.close()

if(data["connected"] == 0):
    wifi_info = "network={\n    ssid='" + data["ssid"] + "'\n" + "    psk='" + data["wifipw"] + "\n    key_mgmt=WPA=PSK\n}"

    file = open("/etc/wpa_supplicant/wpa_supplicant.conf", "a")
    ##file = open("/home/pi/wpa_supplicant.conf", "a")
    file.write(wifi_info)
    file.close()
    new_connecteddata = {"connected": 1}
    data.update(new_connecteddata)
    file = open("config.json", "w")
    json.dump(data, file)
    file.close()
    
savedipaddress = (data["ipaddress"])

if(ip_address == savedipaddress):
    print("ip address has not changed")
else:
    new_ipdata = {"ipaddress": ip_address}
    data.update(new_ipdata)
    file = open("config.json", "w")
    json.dump(data, file)
    file.close()
print(data)

savedhostname = (data["hostname"])
if(savedhostname == hostname):
    print("host name set correctly")
else:
    subprocess.run(['sudo', '/home/pi/modules/change_hostname.sh', savedhostname])


hostname = data["hostname"]
mode = data["mode"]
dbhost = data["dbhost"]
dbuser = data["dbuser"]
dbpassword = data["dbpassword"]
database = data["database"]
serverport = data["serverport"]
pi_inputs = data["piinputs"]
pi_outputs = data["pioutputs"]
exchange = data["exchange"]
alarmqueue = data["alarmqueue"]
ackqueue = data["ackqueue"]
alarm_routingkey = data["alarmroutingkey"]
ack_routingkey = data["ackroutingkey"]
rabbit_userid = data["rabbituser"]
rabbit_password = data["rabbitpass"]

## Update database with online checkin for this host

pidb = db.mysqlconnect(dbhost, dbuser, dbpassword, database)
alarmts = 0
resolvedts = 0
pidb.initial_insert_query(hostID, dbhost, ip_address, time.gmtime(), mode)

if(mode == "server"):
    serverIP = ip_address
else:
    serverIPlist = pidb.server_ip_query()
    serverIPArray = list(serverIPlist)
    serverIP = serverIPArray[0]

print("server ip: ", serverIP)

inputs = list(pi_inputs)
outputs = list(pi_outputs)
pidevice = pi.raspberrypi(pi_inputs, pi_outputs)
qdatahandler = qdata.queuedata(hostID, ip_address)
soc = sock.comms(serverIP, serverport, mode)

def processtrigger():
    global alarmts, resolvedts
    timestamp = time.gmtime()
    newts = calendar.timegm(timestamp)
    if(mode == "server"):
        if(pidevice.getalarmstatus() == False):
            pidevice.setalarmstatus(True)
            alarmts = newts
            pidb.add_alarm(alarmts)
            print("new alarmts:",alarmts)
    else:
        if(pidevice.getalarmstatus() == True):
            pidevice.setalarmstatus(False)
            pidevice.alarmstate(False)
            resolvedts = newts
            print("new resolvedts:", resolvedts)



def infloop():
    while True:
        pidevice.awaitedge(inputs[0])        
        print("button pushed: ", inputs[0])
        processtrigger()
        time.sleep(1)



def connecttoserver():
    global alarmts, resolvedts
    soc = sock.comms(serverIP, serverport, mode)
    soc.connect()
    serverdata = soc.read()
    returnlist = qdatahandler.parse_data(serverdata)
    elements = list(returnlist)
    alarmID = elements[0]
    hostID = elements[1]
    resolvedStatus = elements[2]
    reply = ""
    if(alarmID == alarmts and resolvedStatus == resolvedts):
        print("heartbeat detected")
    elif(alarmID > alarmts and resolvedStatus < alarmID):
        alarmts = alarmID
        print("turning on alarm")
        pidevice.setalarmstatus(True)
        pidevice.alarmstate(True)
    elif(alarmID > alarmts):
        alarmts = alarmID
        resolvedts = resolvedStatus
    elif(resolvedStatus > resolvedts):
        pidevice.setalarmstatus(False)
        pidevice.alarmstate(False)
        resolvedts = resolvedStatus
    else:
        print("Device data: alarmID:", alarmts, "resolutionID:", resolvedts)
        print("Server data: alarmID:", alarmID, "resolutionID:", resolvedStatus)
    reply = qdatahandler.create_heartbeat(alarmts, resolvedts)
    soc.write(reply)
    soc.clientclosesoc()
    pidb.checkin(ip_address, hostname)

def connecttoclient():
    global alarmts, resolvedts
    heartbeat = qdatahandler.create_heartbeat(alarmts, resolvedts)
    
    soc.acceptconnection()
    soc.write(heartbeat)
    data = soc.read()
    returnlist = qdatahandler.parse_data(data)
    elements = list(returnlist)
    resolved = elements[2]
    hostid = elements[1]
    alarmid = elements[0]
    if(resolved > resolvedts and pidevice.getalarmstatus() == True):
        resolvedts = resolved
        pidevice.setalarmstatus(False)
        timestamp = time.gmtime()
        resolutiontime = calendar.timegm(timestamp)
        pidb.resolve_alarm_status(hostid, alarmts)
                
    soc.servercloseconn()
    pidb.checkin(ip_address, hostname)

        

def startprocess():
    if(mode == "server"):
        while(True):
            connecttoclient()
    else:
        while(True):
            connecttoserver()
            time.sleep(2)

    



    


        


awaitinput1 = threading.Thread(target=infloop)
awaitinput1.start()

startconnect = threading.Thread(target=startprocess)
startconnect.start()


