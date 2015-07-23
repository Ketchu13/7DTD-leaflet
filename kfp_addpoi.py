 #!/usr/bin/env python
# -*- coding: utf-8 -*-
# This file is part of 7dtd-leaflet.
#
# 7dtd-leaflet is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# 7dtd-leaflet is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with 7dtd-leaflet. If not, see <http://www.gnu.org/licenses/>.
#
# Source code hosted at:
#    7dtd-leaflet:            https://github.com/nicolas-f/7DTD-leaflet
#    7dtd-leaflet+POI:   https://github.com/Ketchu13/7DTD-leaflet
#
#
# @author Nicolas Fortin github@nettrader.fr https://github.com/nicolas-f
# @author Nicolas Grimaud ketchu13@hotmail.com https://github.com/ketchu13
 
import socket
import sys
import getopt
import xml.etree.ElementTree as ET
import re
import os

def usage():
    print "Usage:"
    print " -i \"127.0.0.1\":\t The server ip..."
    print " -p 8081:\t\t The server port number..."
    print " -z \"CHANGEME\":\t The server password..."
    print " -w \"C:\\...\\whitelist.xml\":\t\t Authorized users list path..."
    print " -k \"C:\\...\\POIList.xml\":\t\t POI list xml..."
    print " -v 1:\t\t\t\t Show received data (0=False, 1=True)..."

def writePoi(x,psdR,sid,poiName,loc):
     try:
         old = readPoi(x)
         with open(x, "w") as f:
             f.write(old + '\n<poi sname=\"' + psdR + '\" steamId=\"' + sid + '\" pname=\"' + poiName + '\" pos=\"' + loc[0] + ',0,' + loc[2] + '\" icon=\"farm\" />\n</poilist>')
             return True
     except IOError:
         return False

def readPoi(x):
     try:
         print x
         with open(x, "r") as f:
             s = ''.join(f.readlines()[:-1])[:-1]
             if len(s) <=0:
                 s = '<poilist>\n'
             print f.readlines()
             return s
     except IOError:
         print "error"


def addPoi(x,psdR,sid,poiName,loc,sock):
     try:
         if writePoi(x,psdR,sid,poiName,loc):
             print 'Poi \"' + poiName + '\" added by ' + psdR
             sock.sendall('say \"[00FF00]' + psdR +', Poi Name: ' + poiName + ' added successfully.\"\n')
         else:
             print 'Poi \"' + poiName + '\" non added. Error... Requested by ' + psdR
             sock.sendall('say \"[00FF00]' + psdR +', error during reading or writing data. Contact an admin.\"\n')
     except IOError:
         print "error"
def selFile(opts):
    try:
        import tkFileDialog
        from Tkinter import Tk
        root = Tk()
        root.withdraw()
        return tkFileDialog.askopenfilename(**opts)
    except ImportError:
        usage()
        exit(-1)

def main():
    sPass = 'CHANGEME'
    sIp = '127.0.0.1'
    sPort = 8081
    wLPath = None #"D:/Inventories/cgi-bin/data.xml" #Whitelist for adding a POI
    alwd = False
    adp = False
    verbose = None
    psdR = None
    poiName = None
    poiPath = None
    loc = None
    ap = '/addpoi '
    tfd = [" joined the game", " left the game", " killed player"]
    try:
        for opt, value in getopt.getopt(sys.argv[1:], "i:p:z:w:k:v")[0]:
            if opt == "-i":
                sIp = value
            elif opt == "-p":
                sPort = int(value)
            elif opt == "-z":
                sPass = value
            elif opt == "-w":
                wLPath = value
            elif opt == "-k":
                poiPath = value
            elif opt == "-v":
                verbose = value
            print 'opt: ' + opt
    except getopt.error, msg:
        usage()
        raw_input()
        exit(-1)

    if wLPath is None:# Show gui to select poi whitelist folder
        wLPath = selFile({"initialdir": os.path.expanduser("~\\Documents\\7 Days To Die\\Saves\\Random Gen\\"),
                    "title": "Choose the Whiteliste that contain autorised users infos."})

    if len(wLPath) == 0:
        print "You must define the leaflet users whitelist."
        exit(-1)

    if poiPath is None:# Show gui to select poi list.xml path
        poiPath = selFile({"initialdir": os.path.expanduser("~\\Documents\\7 Days To Die\\Saves\\Random Gen\\"),
                    "title": "Choose the POIList.xml path."})

    if len(poiPath) == 0:
        print "You must define the leaflet poi list."
        exit(-1)

    try:
        sAddress = (sIp, sPort)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print >>sys.stderr, 'Connecting to %s port %s' % sAddress
        sock.connect(sAddress)
    except socket.error, msg:
        usage()
        print msg
        raw_input()
        exit(-1)
    try:
        while 1:
            d = sock.recv(4096)
            s1 = d.replace(b'\n', b'')
            s2 = s1.split(b'\r')
            d = d.decode(encoding='UTF-8', errors='ignore')
            if 'Please enter password:' in d:
                print >>sys.stderr, 'Connected...\nSending password...'
                sock.sendall(sPass + '\n')
            else:
                for s in s2:
                     if len(s) >= 5:
                         if 'Logon successful.' in d:
                            print >>sys.stderr, 'Logon successful...'
                            sock.sendall('lp\n')
                         elif verbose:
                             print s
                         if 'GMSG:' in s: #chat msg
                             psdRTp =  s[s.find('GMSG:')+6:]
                             tfd = [' joined the game',' left the game',' killed player']
                             skip = False
                             for ik in range(0,len(tfd)):
                                 if tfd[ik] in s:
                                     psdRCt = psdRTp[:psdRTp.find(tfd[ik])]
                                     skip = True
                             if skip:
                                 print ''#TODO gen current user tiles if deco
                             elif ap in s:
                                 adp = True
                                 sock.sendall('lp\n')
                                 psdRPOI = psdRTp[:psdRTp.find(': ')]
                                 # print 'psdrPOI ' + psdRTp
                                 poiName = s[s.find(ap)+len(ap):]
                                 if re.search(r'^[A-Za-z0-9Ü-ü_ \-]{3,25}$', poiName):
                                     print 'Adding a POI is requested by '+psdRPOI+"."
                                     psdR = psdRPOI
                                 else:
                                     print 'Bad Poi name requested by '+psdRPOI
                                     sock.sendall('say \"[FF0000]' + psdRPOI +', The Poi Name must contain between 3 and 25 alphanumerics characters .\"\n')
                         elif ". id=" in  s and adp:
                             sid = ""
                             i = s.find(', ')
                             j = s.find(', pos=(')
                             psd = s[i+2:j]
                             if psdR == psd and not psdR == None:
                                 adp = False
                                 # gId = s[s.find('. id=')+5:i]
                                 # print "gameId: " + gId
                                 l = s.find('steamid=')
                                 sid = s[l+8:s.find(',',l)]
                                 locTp = s[j+7:]
                                 loc = locTp[:locTp.find('), rot')].split(', ')
                                 t = ET.parse(wLPath)
                                 r = t.getroot()
                                 for u in r.findall('user'):
                                     if u.get('steamId') == sid and u.get('rank') >= '1' and u.get('allowed') == '1':
                                                 addPoi(poiPath,psdR,sid,poiName,loc,sock)
                                     else:
                                         print 'Bad user \"' + psdR + '\" steamId: ' + sid
                                         sock.sendall('say \"[FF0000]' + psdRPOI +', your are not allowed to add a poi.\"\n')

    except KeyboardInterrupt:
        print "Fini !"
    finally:
        print "Server done..."

if __name__ == "__main__":
    main()
