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

import getopt
import os
import re
import signal
import socket
import sys
from threading import Timer
from threading import Thread
import threading
import time

import xml.etree.ElementTree as ET

class KFP_AddPOI(threading.Thread):
    def usage(self):
        print "This program extract and merge map tiles of all players.Then write it in a folder with verious zoom"
        print " levels. In order to hide player bases, this program keep only the oldest version of each tile by default."
        print    " By providing the Server telnet address and password this software run in background and is able to do the"
        print    " following features:\n" 
        print    " - Update tiles when a player disconnect\n" 
        print    " - Add Poi when a whitelisted user say /addpoi title\n" 
        print    " - Update players csv coordinates file\n"
        print "Usage:"
        print "map_reader -g XX [options]"
        print " -g \"C:\\Users..\":\t The folder that contain .map files"
        print " -t \"tiles\":\t\t The folder that will contain tiles (Optional)"
        print " -z 8:\t\t\t\t Zoom level 4-n. Number of tiles to extract around position 0,0 of map." 
        print      " It is in the form of 4^n tiles.It will extract a grid of 2^n*16 tiles on each side.(Optional)"
        print " -s telnethost:port \t7DTD server ip and port (telnet port, default 8081) (Optional)"
        print " -p CHANGEME Password of telnet, default is CHANGEME (Optional)"
        print " -i True \t Do not read /addpoi command of players"
        print " -x True \t Do not write players track in csv files"
        print " -h 8080 Http Server Port(default 8081) (Optional)"
        print " -w \"C:\\...\\xml\\POIwhitelist.xml\":\t\t Authorized users list path..."
        print " -k \"C:\\...\\xml\\POIList.xml\":\t\t POI list xml..."
        print " -v True \t\t\t\t Show received data (0=False, 1=True)..."
        print " -c \"www\":\t\t The folder that contain your index.html (Optional)"
        print " -newest Keep track of updates and write the last version of tiles. This will show players bases on map.(Optional)"
        print " -b gui:\t\t Use Gui version (Optional)"

    def __init__(self,parent):
        threading.Thread.__init__(self)
        self.parent = parent
        self.settings = self.parent.settings

        if self.settings['wLPath'] is None:  # Show gui to select poi whitelist folder
            self.settings['wLPath'] = self.selFile({"initialdir": os.path.expanduser("~\\Documents\\7 Days To Die\\Saves\\Random Gen\\"),
                                               "title": "Choose the Whiteliste that contain autorised users infos."})

        if len(self.settings['wLPath']) == 0:
            print "You must define the leaflet users whitelist."
            exit(-1)

        if self.settings['poiPath'] is None:  # Show gui to select poi list.xml path
            self.settings['poiPath'] = self.selFile({"initialdir": os.path.expanduser("~\\Documents\\7 Days To Die\\Saves\\Random Gen\\"),
                        "title": "Choose the POIList.xml path."})

        if len(self.settings['poiPath']) == 0:
            print "You must define the leaflet poi list."
            exit(-1)

        self.parent = parent
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
        sAdress = (self.settings['sIp'] , int(self.settings['sPort']))
        self.sock.connect(sAdress)
        self.th_R = self.ThreadReception(self.sock, self)
        self.th_R.start()

    def sendAllData(self, value):
            s = self.sendData(self.sock, value)
            s.start()
            s.join()

    def rfrshPlyLst(self):
            t = Timer(59.0, self.rfrshPlyLst)
            t.start()
            self.sendAllData('lp\n')

    class ThreadReception(threading.Thread):
        def __init__(self, sock, parent):
            threading.Thread.__init__(self)
            self.sock = sock  # réf. du socket de connexion
            self.parent = parent
            self.exiter = False

        def exite(self):
            if not self.exiter:
                self.exiter = True

        def writePoi(self, x, psdR, sid, poiName, loc):
             try:
                 old = self.readPoi(x)
                 with open(x, "w") as f:
                     f.write(old + '\n<poi sname=\"' + psdR + '\" steamId=\"' + sid + '\" pname=\"' + poiName + '\" pos=\"' + loc + '\" icon=\"farm\" />\n</poilist>')
                 old = self.readPoi(x)   
                 return True
             except IOError:
                 return False

        def readPoi(self, x):
             try:
                 with open(x, "r") as f:
                     s = ''.join(f.readlines()[:-1])[:-1]
                     if len(s) <= 0:
                         s = '<poilist>\n'
                     return s
             except IOError as e:
                 print ("error", e)

        def addPoi(self, x, psdR, sid, poiName, loc, sock):
             try:
                 if self.writePoi(x, psdR, sid, poiName, loc):
                     #self.parent.updatePoi('Poi \"' + poiName + '\" added by ' + psdR)
                     self.parent.sendAllData('say \"[00FF00]' + psdR + ', Poi Name: ' + poiName + ' added successfully.\"\n')
                 else:
                     #self.parent.updatePoi('Poi \"' + poiName + '\" non added. Error... Requested by ' + psdR)
                     self.parent.sendAllData('say \"[00FF00]' + psdR + ', error during reading or writing data. Contact an admin.\"\n')
             except IOError:
                 print ("error", e)

        def run(self):
            sPass = self.parent.parent.settings['sPass']
            sIp = self.parent.parent.settings['sIp']
            sPort = self.parent.parent.settings['sPort']
            wLPath = str(self.parent.parent.settings['wLPath'])
            alwd = False
            adp = False
            verbose = bool(self.parent.parent.settings['verbose'])
            psdR = None
            poiName = None
            poiPath = self.parent.parent.settings['poiPath']
            listUsers = []
            loc = None
            ap = '/addpoi '
            tfd = [" joined the game", " left the game", " killed player"]
            loged = False
            while not self.exiter:
                    s = None
                    s1 = None
                    s2 = None
                    d = None
                    d = self.sock.recv(4096)
                    d = d.decode(encoding='UTF-8', errors='ignore')
                    s1 = d.replace(b'\n', b'')
                    s2 = s1.split(b'\r')

                    if 'Please enter password:' in d:
                        #self.parent.update('Connected...\nSending password...')
                        self.parent.sendAllData(sPass)
                    else:
                        for s in s2:
                             if len(s) >= 5:
                                 nn = 'Player disconnected: EntityID='
                                 nn2 = ', PlayerID=\''
                                 if nn in s:
                                     steamID = s[s.find(nn2)+len(nn2):s.find('\', OwnerID=\'')]
                                     mp = self.parent.mapR(self.parent,steamID)  
                                     mp.start() 
                                 if 'Logon successful.' in d and not loged:
                                     loged = True
                                     self.parent.sendAllData('lp')
                                     self.parent.rfrshPlyLst()
                                 elif verbose:
                                     #self.parent.update(s)
                                     print s
                                 if 'GMSG:' in s:  # chat msg
                                     psdRTp = s[s.find('GMSG:') + 6:]
                                     tfd = [' joined the game', ' left the game', ' killed player']
                                     skip = False
                                     for ik in range(0, len(tfd)):
                                         if tfd[ik] in s:
                                             psdRCt = psdRTp[:psdRTp.find(tfd[ik])]
                                             if ik == 1:
                                                 skip = True
                                     if skip:
                                         self.parent.sendAllData('lp')
                                     elif ap in s:
                                         adp = True
                                         self.parent.sendAllData('lp')
                                         psdRPOI = psdRTp[:psdRTp.find(': ')]
                                         poiName = s[s.find(ap) + len(ap):]
                                         if re.search(r'^[A-Za-z0-9Ü-ü_ \-]{3,25}$', poiName):
                                             #self.parent.updatePoi('Adding a POI is requested by ' + psdRPOI + ".")
                                             psdR = psdRPOI
                                         else:
                                             #self.parent.updatePoi('Bad Poi name requested by ' + psdRPOI)
                                             self.parent.sendAllData('say \"[FF0000]' + psdRPOI + ', The Poi Name must contain between 3 and 25 alphanumerics characters .\"')
                                 elif ". id=" in s:
                                     sid = ""
                                     fg = s[:s.find('. id=')]
                                     i = s.find(', ')
                                     j = s.find(', pos=(')
                                     psd = s[i + 2:j]
                                     if psd in listUsers:
                                         listUsers.remove(psd)
                                     listUsers.insert(int(fg), psd)
                                     #self.parent.listUsers(listUsers)
                                     gId = s[s.find('. id=') + 5:i]
                                     l = s.find('steamid=')
                                     sid = s[l + 8:s.find(',', l)]
                                     locTp = s[j + 7:]
                                     loc = locTp[:locTp.find('), rot')]#.split(', ')
                                     locx = int(float(loc.split(', ')[0]))
                                     locy = int(float(loc.split(', ')[2]))
                                     if self.parent.parent.settings['ignTrack']:
                                        tracks = [(psd , locx, locy)]
                                        self.th_tracks = self.parent.updateTracks_csv(self,tracks)
                                        self.th_tracks.start()
                                     if adp:
                                         if psdR == psd and not psdR == None:
                                             adp = False
                                             t = ET.parse(wLPath)
                                             r = t.getroot()
                                             for u in r.findall('user'):
                                                 if u.get('steamId') == sid and u.get('rank') >= '1' and u.get('allowed') == '1':
                                                     self.addPoi(poiPath, psdR, sid, poiName, str(locx) + ", " + str(locy), self.sock)
                                                 else:
                                                     #self.parent.updatePoi('Bad user \"' + psdR + '\" steamId: ' + sid)
                                                     self.parent.sendAllData('say \"[FF0000]' + psdRPOI + ', your are not allowed to add a poi.\"')
            print u"Client arrêté. connexion interrompue."
            self.sock.close()

    class updateTracks_csv(threading.Thread):
        def __init__(self,parent,value):
            threading.Thread.__init__(self)
            self.parent = parent
            self.value = value
        def run(self):
            try:
                import csv
                Fn = (r".\players\tracks.csv")
                f = open(Fn, 'ab')
                w = csv.writer(f)
                w.writerows(self.value)
                f.close
            except Exception as e:
                print e

    class sendData(threading.Thread):
        def __init__(self, sock, value):
            threading.Thread.__init__(self)
            self.sock = sock
            self.value = value 
        def run(self):
            try:
                self.sock.send(self.value + '\n')
            except Exception as e:
                print e

    def run(self):
        pass

    class getNameBySid(threading.Thread):
        def __init__(self, parent, value):
            threading.Thread.__init__(self)
            self.sId = value
            self.parent = parent
        def run(self):
            t = ET.parse('./xml/PlayersList2.xml')
            r = t.getroot()
            found= False
            for player in r.findall('player'):
                try:
                    steamId = player.get('steamId')
                    
                    if steamId == self.sId:
                       found = True
                       self.parent.parent.updateKL("SteamId: " + steamId + " - Username: " + player.get('name'))
                except Exception as e:
                    print e
            if not found:
                self.parent.parent.updateKL("SteamId: " + self.sId + " - Username: unknow")

    class mapR(threading.Thread):
        def __init__(self, parent, value):
            threading.Thread.__init__(self)
            self.parent = parent
            self.value = value 
        def run(self):
            self.parent.parent.copyMapFile(self.parent.parent.settings['game_player_path'], self.value+".map")
            self.parent.parent.map_files = self.parent.parent.read_folder("Map")
            self.parent.parent.create_tiles(self.parent.parent.map_files, self.parent.parent.settings['tile_path'], self.parent.parent.settings['tile_zoom'], self.parent.parent.settings['store_history'])
