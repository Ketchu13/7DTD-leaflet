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
        print " By providing the Server telnet address and password this software run in background and is able to do the"
        print " following features:\n"
        print " - Update tiles when a player disconnect\n"
        print " - Add Poi when a whitelisted user say /addpoi title\n"
        print " - Update players csv coordinates file\n"
        print "Usage:"
        print "map_reader -g XX [options]"
        print " -g \"C:\\Users..\":\t The folder that contain .map files"
        print " -t \"tiles\":\t\t The folder that will contain tiles (Optional)"
        print " -z 8:\t\t\t\t Zoom level 4-n. Number of tiles to extract around position 0,0 of map." 
        print " It is in the form of 4^n tiles.It will extract a grid of 2^n*16 tiles on each side.(Optional)"
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
            self.settings['wLPath'] = self.select_file({"initialdir": os.path.expanduser("~\\Documents\\7 Days To Die\\Saves\\Random Gen\\"),
                                               "title": "Choose the Whiteliste that contain autorised users infos."})

        if len(self.settings['wLPath']) == 0:
            print "You must define the leaflet users whitelist."
            exit(-1)

        if self.settings['poiPath'] is None:  # Show gui to select poi list.xml path
            self.settings['poiPath'] = self.select_file({"initialdir": os.path.expanduser("~\\Documents\\7 Days To Die\\Saves\\Random Gen\\"),
                        "title": "Choose the POIList.xml path."})

        if len(self.settings['poiPath']) == 0:
            print "You must define the leaflet poi list."
            exit(-1)

        self.parent = parent
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((self.settings['sIp'] , int(self.settings['sPort'])))
        self.thread_reception = self.ThreadReception(self.sock, self)
        self.thread_reception.start()

    def select_file(self,opts):
        try:
            import tkFileDialog
            from Tkinter import Tk
            root = Tk()
            root.withdraw()
            return tkFileDialog.askopenfilename(**opts)
        except ImportError:
            self.usage()
            exit(-1)

    class ThreadReception(threading.Thread):
        def __init__(self, sock, parent):
            threading.Thread.__init__(self)
            self.sock = sock
            self.parent = parent
            self.exiter = False

        def exite(self):
            if not self.exiter:
                self.exiter = True

        def refresh_players_list(self):
            try:
                print "\n\tSend lp\n\n"
                self.sock.sendall('lp\n')
                t = Timer(20.0, self.refresh_players_list)
                t.start()
            except Exception as e:
                print "Error: " + str(e)

        @staticmethod
        def writepoi(poilist_path, pseudo_request, sid, poiname, poi_location):
            try:
                print "poilist_path: " + poilist_path + "\n"
                with open(poilist_path, "r") as f:
                    poilist_src = ''.join(f.readlines()[:-1])[:-1]
                    print "poilist_src: " + poilist_src + "\n"
                    if len(poilist_src) <= 0:
                        print "poilist_src2: " + poilist_src
                        poilist_src = '<poilist>\n'
                with open(poilist_path, "r+") as f:
                    f.write(poilist_src + '\n' +
                    '<poi sname=\"' + pseudo_request +
                    '\" steamId=\"' + sid +
                    '\" pname=\"' + poiname +
                    '\" pos=\"' + poi_location +
                    '\" icon=\"farm\" />\n' +
                    '</poilist>')
                return True
            except IOError as e:
                print ("\n\nError in writepoi: ", e)
                return False

        def addpoi(self, poilist_path, pseudo_request, sid, poiname, poi_location):
            try:
                if self.writepoi(poilist_path, pseudo_request, sid, poiname, poi_location):
                    self.sock.sendall('say \"[00FF00]' + pseudo_request +
                                      ', Poi Name: ' + poiname + ' added successfully.\"\n')
                else:
                    self.sock.sendall('say \"[00FF00]' + pseudo_request +
                                      ', error during reading or writing data. Contact an admin.\"\n')
            except IOError as e:
                print ("Error in addpoi: ", e)

        def run(self):
            whitelist_path = str(self.parent.parent.settings['wLPath'])
            verbose = bool(self.parent.parent.settings['verbose'])
            server_pass = self.parent.parent.settings['sPass']
            poi_path = self.parent.parent.settings['poiPath']
            adp = False
            pseudo_poi = ''
            poiname = None
            loged = False
            pseudo_request = None

            while not self.exiter:
                """str_line = None
                s1 = None
                s2 = None"""
                data_received = self.sock.recv(4096)
                data_received = data_received.decode(encoding='UTF-8', errors='ignore')
                s1 = data_received.replace(b'\n', b'')
                s2 = s1.split(b'\r')

                if 'Please enter password:' in data_received:  # connected with 7dtd server
                    self.sock.sendall(server_pass+'\n')
                else:
                    for str_line in s2:
                        if len(str_line) >= 5:
                            nn = 'Player disconnected: EntityID='
                            nn2 = ', PlayerID=\''
                            if nn in str_line:  # check new player connection
                                steamid = str_line[str_line.find(nn2)+len(nn2):str_line.find('\', OwnerID=\'')]  # get steamid
                                mp = self.parent.GenUserMap(self.parent,steamid)  # gen this user tiles map
                                mp.start()
                            if 'Logon successful.' in data_received and not loged:  # password ok
                                loged = True
                                self.sock.sendall('lp\n')  # request player list
                                self.refresh_players_list()  # add a timer fo refresh player list every X s
                            elif verbose:
                                print str_line
                            if 'GMSG:' in str_line:  # receive a chat msg
                                pseudo_temp = str_line[str_line.find('GMSG:') + 6:]
                                msg_list = [' joined the game', ' left the game', ' killed player']
                                skip = False
                                for ik in range(0, len(msg_list)):  # parse server chat message
                                    if msg_list[ik] in str_line:
                                        #  pseudo_event = pseudo_temp[:pseudo_temp.find(msg_list[ik])]
                                        if ik == 1:
                                            skip = True
                                addpoi_cmd = '/addpoi'
                                if skip:  # refresh players infos
                                    self.sock.sendall('lp\n')
                                elif addpoi_cmd in str_line:
                                    adp = True
                                    self.sock.sendall('lp\n')
                                    pseudo_poi = pseudo_temp[:pseudo_temp.find(': ')]
                                    poiname = str_line[str_line.find(addpoi_cmd) + len(addpoi_cmd):]
                                    if re.search(r'^[A-Za-z0-9Ü-ü_ \-]{3,25}$', poiname):
                                        pseudo_request = pseudo_poi
                                    else:
                                        self.sock.sendAll('say \"[FF0000]' +
                                                          pseudo_poi +
                                                          ', The Poi Name must contain between 3 ' +
                                                          'and 25 alphanumerics characters .\"')
                            elif '. id=' in str_line:
                                i = str_line.find(', ')
                                j = str_line.find(', pos=(')
                                pseudo = str_line[i + 2:j]
                                sid_temp = str_line.find('steamid=')
                                sid = str_line[sid_temp + 8:str_line.find(',', sid_temp)]
                                loc_temp = str_line[j + 7:]
                                user_location = loc_temp[:loc_temp.find('), rot')]
                                poiloc_y = int(float(user_location.split(', ')[0]))
                                poiloc_x = int(float(user_location.split(', ')[2]))
                                if self.parent.parent.settings['ignTrack']:
                                    tracks = [(pseudo, poiloc_x, poiloc_y)]
                                    try:
                                        import csv
                                        tracks_path = os.path.join('.', 'players', 'tracks.csv')
                                        with open(tracks_path, 'ab') as f:
                                            w = csv.writer(f)
                                            w.writerows(tracks)
                                    except Exception as e:
                                        print e
                                if adp and pseudo_request == pseudo and pseudo_request is not None:
                                        adp = False
                                        t = ET.parse(whitelist_path)
                                        r = t.getroot()
                                        for u in r.findall('user'):
                                            if u.get('steamId') == sid and \
                                                            u.get('rank') >= '1' and \
                                                            u.get('allowed') == '1':
                                                self.addpoi(poi_path, pseudo_request, sid, poiname, str(poiloc_x) + ", "
                                                            + str(poiloc_y))
                                            else:
                                                self.sock.sendall('say \"[FF0000]' +
                                                                  pseudo_poi +
                                                                  ', your are not allowed to add a poi.\"')
            print u"Client arrêté. connexion interrompue."
            self.sock.close()

    class GenUserMap(threading.Thread):
        def __init__(self, parent, value):
            threading.Thread.__init__(self)
            self.parent = parent
            self.value = value

        def run(self):
            self.parent.parent.copy_map_file(self.parent.parent.settings['game_player_path'],
                                             self.value + ".map")
            self.parent.parent.map_files = self.parent.parent.read_folder("Map")
            self.parent.parent.create_tiles(self.parent.parent.map_files,
                                            self.parent.parent.settings['tile_path'],
                                            self.parent.parent.settings['tile_zoom'],
                                            self.parent.parent.settings['store_history'])
