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
#    7dtd-leaflet+POI:        https://github.com/Ketchu13/7DTD-leaflet
#
#
# @author Nicolas Fortin github@nettrader.fr https://github.com/nicolas-f
# @author Nicolas Grimaud ketchu13@hotmail.com https://github.com/ketchu13

import ftplib as ftp
from cStringIO import StringIO
import os
import socket
from threading import Timer
import threading
import time
import xml.etree.ElementTree as ET

from libs.TabPages import *


class KFP_AddPOIGui(threading.Thread):
    @staticmethod
    def usage():
        print "This program extract and merge map tiles of all players.Then write it in a folder with various zoom"
        print " levels. In order to hide player bases, this program keep only the oldest version of each tile by default."
        print " By providing the Server telnet address and password this software run in background and is able to do the"
        print " following features:\n"
        print " - Update tiles when a player disconnect\n"
        print " - Add Poi when an allowed user say /addpoi title\n"
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
        print " -f FTPHost:UserName:PassWord \t FTP server connection infos (Optional)"

    def __init__(self, parent):
        threading.Thread.__init__(self)
        self.fen = self.AddPOI_GUI(self)
        self.parent = parent
        self.settings = self.parent.settings

        if self.settings['wLPath'] is None:  # Show gui to select poi whitelist folder
            self.settings['wLPath'] = self.select_file(
                {"initialdir": os.path.expanduser("~\\Documents\\7 Days To Die\\Saves\\Random Gen\\"),
                 "title": "Choose the Whiteliste that contain autorised users infos."})
        if len(self.settings['wLPath']) == 0:
            print "You must define the leaflet users whitelist."
            exit(-1)

        if self.settings['poiPath'] is None:  # Show gui to select poi list.xml path
            self.settings['poiPath'] = self.select_file(
                {"initialdir": os.path.expanduser("~\\Documents\\7 Days To Die\\Saves\\Random Gen\\"),
                 "title": "Choose the POIList.xml path."})

        if len(self.settings['poiPath']) == 0:
            print "You must define the leaflet poi list."
            exit(-1)

    def run(self):
        self.fen.start()

    def select_file(self, opts):
        try:
            import tkFileDialog
            from Tkinter import Tk
            root = Tk()
            root.withdraw()
            return tkFileDialog.askopenfilename(**opts)
        except ImportError:
            print ('Error in select_file')
            self.usage()
            exit(-1)

    class ThreadReception(threading.Thread):
        def __init__(self, sock, parent):
            threading.Thread.__init__(self)
            self.sock = sock
            self.parent = parent
            self.exiter = False
            print('ThreadReception __inited__...')  # print "receive thread"

        def exite(self):
            if not self.exiter:
                self.exiter = True
                print('ThreadReception exit...')

        def refresh_players_list(self):
            try:
                print('ThreadReception send lp every 5s\n')
                self.sock.sendall('lp\n')
                t = Timer(15.0, self.refresh_players_list)  # !! 5 Secondes !!
                t.start()
            except Exception as e:
                print "Error in refresh_player: " + str(e)

        def writepoi(self, poilist_path, pseudo_request, sid, poiname, poi_location):
            try:
                with open(poilist_path, "r") as f:
                    poilist_src = ''.join(f.readlines()[:-1])[:-1]
                    if len(poilist_src) <= 0:
                        poilist_src = '<poilist>\n'
                        print("\tPOIList.xml successfully loaded..")
                with open(poilist_path, "r+") as f:
                    str_poi = '<poi userName=\"' + pseudo_request + \
                              '\" steamId=\"' + sid + \
                              '\" pname=\"' + poiname + \
                              '\" pos=\"' + poi_location + \
                              '\" icon=\"farm\" />\n' + '</poilist>'
                    f.write(poilist_src + '\n' + str_poi)
                    self.parent.update_poi_list(str_poi)
                    print("\tPoi added and POIList.xml successfully saved..")
                return True
            except IOError as e:
                print ("Error in writepoi: ", e)
                return False

        def addpoi(self, poilist_path, pseudo_request, sid, poiname, poi_location):
            try:
                if self.writepoi(poilist_path, pseudo_request, sid, poiname, poi_location):
                    self.parent.updatePoi('Poi \"' + poiname + '\" added by ' + pseudo_request)
                    self.sock.sendall('say \"[00FF00]' + pseudo_request +
                                      ', Poi Name: ' + poiname + ' added successfully.\"\n')
                else:
                    self.parent.updatePoi('Poi \"' + poiname + '\" non added. Error... Requested by ' + pseudo_request)
                    self.sock.sendall('say \"[00FF00]' + pseudo_request +
                                      ', error during reading or writing data. Contact an admin.\"\n')
            except IOError as e:
                print ("\tError in addpoi: ", e)

        def run(self):
            print('\tThreadReception is running\n')
            server_pass = self.parent.parent.settings['sPass']
            whitelist_path = str(self.parent.parent.settings['wLPath'])
            adp = False
            verbose = bool(self.parent.parent.settings['verbose'])
            pseudo_request = None
            poiname = None
            poi_path = self.parent.parent.settings['poiPath']
            list_users = []
            ap = '/addpoi '
            loged = False
            while not self.exiter:
                """str_line = None
                s1 = None
                s2 = None"""
                data_received = self.sock.recv(4096)
                data_received = data_received.decode(encoding='UTF-8', errors='ignore')
                s1 = data_received.replace(b'\n', b'')
                s2 = s1.split(b'\r')

                if 'Please enter password:' in data_received:
                    self.parent.update('Connected...\nSending password...')
                    self.parent.sendAllData(server_pass)
                else:
                    for str_line in s2:
                        if len(str_line) >= 5:
                            nn = 'Player disconnected: EntityID='
                            nn2 = ', PlayerID=\''
                            if verbose:
                                self.parent.update(str_line)
                            if nn in str_line:  # check new player connection
                                steamid = str_line[
                                          str_line.find(nn2) + len(nn2):str_line.find('\', OwnerID=\'')]  # get steamid
                                mp = self.parent.parent.GenUserMap(self.parent.parent, steamid)
                                mp.start()
                            elif 'Logon successful.' in str_line and not loged:
                                loged = True
                                self.parent.sendAllData('lp')  # request player list
                                self.parent.refresh_players_list()  # add a timer fo refresh player list every X s

                            elif 'GMSG:' in str_line:  # receive a chat msg
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
                                    self.parent.sendAllData('lp')
                                elif ap in str_line:
                                    adp = True
                                    self.parent.sendAllData('lp')
                                    pseudo_poi = pseudo_temp[:pseudo_temp.find(': ')]
                                    poiname = str_line[str_line.find(addpoi_cmd) + len(addpoi_cmd):]
                                    if re.search(r'^[A-Za-z0-9Ü-ü_ \-]{3,25}$', poiname):
                                        self.parent.updatePoi('Adding a POI is requested by ' + pseudo_poi + ".")
                                        pseudo_request = pseudo_poi
                                    else:
                                        self.parent.updatePoi('Bad Poi name requested by ' + pseudo_poi)
                                        self.parent.sendAllData('say \"[FF0000]' +
                                                                pseudo_poi +
                                                                ', The Poi Name must contain between 3 and 25 alphanumerics characters .\"')
                            elif '. id=' in str_line:
                                fg = str_line[:str_line.find('. id=')]
                                #  gId = str_line[str_line.find('. id=') + 5:i]
                                i = str_line.find(', ')
                                j = str_line.find(', pos=(')
                                pseudo = str_line[i + 2:j]
                                sid_temp = str_line.find('steamid=')
                                sid = str_line[sid_temp + 8:str_line.find(',', sid_temp)]
                                loc_temp = str_line[j + 7:]
                                user_location = loc_temp[:loc_temp.find('), rot')]
                                poiloc_y = int(float(user_location.split(', ')[0]))
                                poiloc_x = int(float(user_location.split(', ')[2]))
                                if pseudo in list_users:
                                    list_users.remove(pseudo)
                                list_users.insert(int(fg), pseudo)
                                self.parent.listUsers(list_users)
                                if self.parent.parent.settings['ignTrack']:
                                    tracks = [(pseudo, poiloc_x, poiloc_y)]
                                    try:
                                        import csv
                                        tracks_path = os.path.join('players', 'tracks.csv')
                                        with open(tracks_path, 'ab') as f:
                                            w = csv.writer(f)
                                            w.writerows(tracks)
                                    except Exception as e:
                                        print e
                                if adp and pseudo_request == pseudo and pseudo_request is not None:
                                    adp = False
                                    t = ET.parse(whitelist_path)
                                    r = t.getroot()
                                    allow = False
                                    for u in r.findall('user'):
                                        if u.get('steamId') == sid and u.get('rank') >= '1' and u.get('allowed') == '1':
                                            self.parent.addPoi(poi_path, pseudo_request, sid, poiname, str(poiloc_x) +
                                                               ", " + str(poiloc_y), self.sock)
                                            allow = True
                                            break
                                    if not allow:
                                        self.parent.updatePoi('Bad user \"' + pseudo_poi + '\" steamId: ' + sid)
                                        self.parent.sendAllData('say \"[FF0000]' +
                                                                pseudo_poi +
                                                                ',sorry, your are not allowed to add a poi.\"')
            print u"Client arrêté. connexion interrompue."
            self.sock.close()

    class Capturing(list):
        def __enter__(self):
            self._stdout = sys.stdout
            sys.stdout = self._stringio = StringIO()
            return self

        def __exit__(self, *args):
            self.extend(self._stringio.getvalue().splitlines())
            sys.stdout = self._stdout

    class KFPFTP(threading.Thread):
        def __init__(self, parent):
            threading.Thread.__init__(self)
            self.parent = parent
            self.FtpInfos = self.parent.parent.settings['FTPInfos'].split(':')
            self.host = self.FtpInfos
            self.connection = ftp.FTP(self.FtpInfos[0], self.FtpInfos[1], self.FtpInfos[2])
            with self.parent.parent.Capturing() as self.output:
                print self.ls()
            for line in self.output:
                self.parent.updateFTP(line)

        def cd(self, rep):
            return self.connection.cwd(rep)

        def ls(self):
            return self.connection.dir()

        def lsd(self, rep):
            return self.connection.dir(rep)

        def getF(self, rep):
            with open(os.path.join('./', rep), "wb") as gfile:
                self.connection.retrbinary('RETR ' + rep, gfile.write)

        def deco(self):
            return self.connection.quit()

        def envoi(self, adresse_fichier):
            _file = open(adresse_fichier, 'rb')
            self.connection.storbinary('STOR ' + adresse_fichier, _file)
            _file.close()

        def rename(self, avant, apres):
            return self.connection.rename(avant, apres)

        def efface(self, fichier):
            return self.connection.delete(fichier)

        def creer_rep(self, nom):
            return self.connection.mkd(nom)

        def sup_rep(self, nom):
            return self.connection.rmd(nom)

        def run(self):
            pass

    class ShowKeyLocation(threading.Thread):
        def __init__(self, parent, value):
            threading.Thread.__init__(self)
            self.parent = parent
            self.value = value

        def run(self):
            t = ET.parse('./xml/players.xml')
            r = t.getroot()
            for player in r.findall('player'):
                try:
                    steamid = player.get('id')
                    try:
                        th = self.parent.parent.getNameBySid(self, steamid)
                        th.start()
                        th.join()
                    except Exception as e:
                        print e
                        pass
                    i = 0
                    for lpBlocks in player.findall('lpblock'):
                        i += 1
                        if self.value is None:
                            self.parent.update_keystones_list('\t\tKeystone ' + str(i) + ': ' + lpBlocks.get('pos'))
                        elif self.value == steamid:
                            self.parent.update_keystones_list('\t\tKeystone ' + str(i) + ': ' + lpBlocks.get('pos'))
                except Exception as e:
                    print e
                    pass

    """ HTTP SERVER """

    class httpServer(threading.Thread):
        def __init__(self, gui):
            threading.Thread.__init__(self)
            self.GUI = gui
            self.host = ''
            self.port = self.GUI.parent.settings['http_server_port']
            self.www = self.GUI.parent.settings['www']
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.keep_running = True

        def run(self):
            # self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                self.GUI.updateHTTP("Launching HTTP server on " + self.host + ":" + str(self.port))
                self.socket.bind((self.host, self.port))
            except Exception:
                ub = False
                while not ub:
                    self.GUI.updateHTTP("Warning: Could not aquite port: " + str(self.port) + "\n")
                    self.GUI.updateHTTP("I will try a higher port")
                    self.port = int(self.port) + 1
                    try:
                        self.GUI.updateHTTP("Launching HTTP server on " + self.host + ":" + str(self.port))
                        self.socket.bind((self.host, self.port))
                        ub = True
                    except Exception:
                        self.GUI.updateHTTP("ERROR: Failed to acquire sockets for ports " + str(self.port))

            self.GUI.updateHTTP("Server successfully acquired the socket with port: " + str(self.port))
            self.GUI.updateHTTP("Press Ctrl+C to shut down the server and exit.")
            self._wait_for_connections()

        def shutdown(self):
            try:
                self.GUI.updateHTTP("Shutting down the server")
                self.socket.shutdown(socket.SHUT_RDWR)
            except Exception as e:
                self.GUI.updateHTTP("Warning: could not shut down the socket. Maybe it was already closed? " + str(e))

        @staticmethod
        def _gen_headers(code):
            h = ''
            if code == 200:
                h = 'HTTP/1.1 200 OK\n'
            elif code == 404:
                h = 'HTTP/1.1 404 Not Found\n'
            current_date = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
            h += 'Date: ' + current_date + '\n'
            h += 'Server: KFP-Python-HTTP-Server\n'
            h += 'Connection: close\n\n'
            return h

        def _wait_for_connections(self):
            while True:
                self.GUI.updateHTTP("Awaiting New connection")
                self.socket.listen(3)
                conn, addr = self.socket.accept()
                data = conn.recv(1024)
                string = bytes.decode(data)
                request_method = string.split(' ')[0]
                self.GUI.updateHTTP("Got connection from:" + str(addr) + " - Request body: " + string.split('\n')[0])
                if (request_method == 'GET') | (request_method == 'HEAD'):
                    filerqt = string.split(' ')
                    filerqt = filerqt[1]
                    filerqt = filerqt.split('?')[0]
                    if filerqt == '/':
                        filerqt = '/index.html'
                    filerqt = self.www + filerqt
                    self.GUI.updateHTTP("Serving web page [" + filerqt + "]")
                    # # Load file content
                    response_content = ''
                    try:
                        file_handler = open(filerqt, 'rb')
                        if request_method == 'GET':
                            response_content = file_handler.read()
                        file_handler.close()
                        response_headers = self._gen_headers(200)
                    except Exception as e:
                        self.GUI.updateHTTP("Warning, file not found. Serving response code 404\n" + str(e))
                        response_headers = self._gen_headers(404)
                        if request_method == 'GET':
                            response_content = b"<html><head>" + \
                                               "<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\">" + \
                                               "</head><body style=\"background-image:url(./images/404.gif);" + \
                                               "background-repeat:no-repeat; background-position:center center;" + \
                                               "color: red;" + \
                                               "background-color:black;\"><h2>KFP ZBot Lite Simple Web Server</h2>" + \
                                               "<!--div>404 - Not Found</div--></body></html>"
                    server_response = response_headers.encode()
                    if request_method == 'GET':
                        server_response += response_content
                    conn.send(server_response)
                    self.GUI.updateHTTP("Closing connection with client")
                    conn.close()
                else:
                    self.GUI.updateHTTP("Unknown HTTP request method: " + request_method)

        def keerunning(self, value):
            self.keep_running = bool(value)

    class AddPOI_GUI(threading.Thread):
        def __init__(self, parent):
            threading.Thread.__init__(self)
            self.parent = parent
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.th_R = self.parent.ThreadReception(self.sock, self)
            print self.th_R.getName()
            self.rootM = Tk()

        def run(self):
            print "before thread reception"
            self.rootM.configure(bg='black')
            self.rootM.title = "ZBot lite py"
            self.tabPage = TabbedPageSet(self.rootM,
                                         page_names=['Logs',
                                                     'AddPoi',
                                                     'POIList.xml',
                                                     'WhiteList',
                                                     'HTTP_Server',
                                                     'Keystones Locations',
                                                     'FTP Client'], bg="#000000", n_rows=0, expand_tabs=True, )
            self.tabPage.pages['Logs'].frame.configure(bg="#000000")
            self.tabPage.pages['AddPoi'].frame.configure(bg="#000000")
            self.tabPage.pages['POIList.xml'].frame.configure(bg="#000000")
            self.tabPage.pages['WhiteList'].frame.configure(bg="#000000")
            self.tabPage.pages['HTTP_Server'].frame.configure(bg="#000000")
            self.tabPage.pages['Keystones Locations'].frame.configure(bg="#000000")
            self.tabPage.pages['FTP Client'].frame.configure(bg="#000000")

            strs1 = StringVar()
            strs2 = StringVar()
            strs3 = StringVar()
            strs4 = StringVar()
            strsp1 = StringVar()
            strsp2 = StringVar()

            strs1.set(self.parent.parent.settings['sPort'])
            strs2.set(self.parent.parent.settings['sIp'])
            strs3.set(self.parent.parent.settings['sPass'])
            strs4.set("say ")
            strsp1.set(self.parent.parent.settings['http_server_port'])
            strsp2.set(int(self.parent.parent.settings['http_server_port']) + 5)

            """7dtd Server Logs Tab"""
            self.label1 = Label(self.tabPage.pages['Logs'].frame, bg="#000000", fg="#ff0000", borderwidth=1,
                                text="Server IP: ", )
            self.label2 = Label(self.tabPage.pages['Logs'].frame, bg="#000000", fg="#ff0000", text="Server Port: ", )
            self.label3 = Label(self.tabPage.pages['Logs'].frame, bg="#000000", fg="#ff0000", text="Server Password:", )
            self.entry_1 = Entry(self.tabPage.pages['Logs'].frame, textvariable=strs4, bg="#000000", fg="#ff0000",
                                 width=0, )
            self.entry2 = Entry(self.tabPage.pages['Logs'].frame, textvariable=strs1, justify="center", relief="flat",
                                width=0, )
            self.entry3 = Entry(self.tabPage.pages['Logs'].frame, textvariable=strs3, justify="center", relief="flat",
                                width=0, show="*")
            self.button1 = Button(self.tabPage.pages['Logs'].frame, text="Connect", command=self.connect)
            self.button2 = Button(self.tabPage.pages['Logs'].frame, text="Send", command=self.send)

            self.sbar1 = Scrollbar(self.tabPage.pages['Logs'].frame)
            self.sbar2 = Scrollbar(self.tabPage.pages['Logs'].frame)

            self.text1 = Text(self.tabPage.pages['Logs'].frame, bg="#000000", fg="#ff0000", height=0, width=0, )
            self.text2 = Text(self.tabPage.pages['Logs'].frame, bg="#000000", fg="#ff0000", height=0, width=0, )
            self.text3 = Text(self.tabPage.pages['Logs'].frame, bg="#000000", fg="#ff0000", height=0, width=0, )

            self.entry4 = Entry(self.tabPage.pages['Logs'].frame, textvariable=strs2, justify="center", relief="flat",
                                width=0, )
            self.sbar1.config(command=self.text1.yview)
            self.sbar1.config(command=self.text2.yview)

            self.label1.grid(in_=self.tabPage.pages['Logs'].frame, column=1, row=1, columnspan=1, ipadx=0, ipady=0,
                             padx=5, pady=5, rowspan=1, sticky="")
            self.entry4.grid(in_=self.tabPage.pages['Logs'].frame, column=2, row=1, columnspan=1, ipadx=0, ipady=0,
                             padx=5, pady=5, rowspan=1, sticky="ew")
            self.label2.grid(in_=self.tabPage.pages['Logs'].frame, column=3, row=1, columnspan=1, ipadx=0, ipady=0,
                             padx=5, pady=5, rowspan=1, sticky="")
            self.entry2.grid(in_=self.tabPage.pages['Logs'].frame, column=4, row=1, columnspan=1, ipadx=0, ipady=0,
                             padx=5, pady=5, rowspan=1, sticky="ew")
            self.label3.grid(in_=self.tabPage.pages['Logs'].frame, column=5, row=1, columnspan=1, ipadx=0, ipady=0,
                             padx=5, pady=5, rowspan=1, sticky="")
            self.entry3.grid(in_=self.tabPage.pages['Logs'].frame, column=6, row=1, columnspan=1, ipadx=0, ipady=0,
                             padx=5, pady=5, rowspan=1, sticky="ew")
            self.button1.grid(in_=self.tabPage.pages['Logs'].frame, column=8, row=1, columnspan=2, ipadx=0, ipady=0,
                              padx=5, pady=5, rowspan=1, sticky="nsew")
            self.text1.grid(in_=self.tabPage.pages['Logs'].frame, column=1, row=2, columnspan=6, rowspan=1, ipadx=5,
                            ipady=0, padx=2, pady=5, sticky="news")
            self.sbar1.grid(in_=self.tabPage.pages['Logs'].frame, column=7, row=2, columnspan=1, rowspan=1, ipadx=0,
                            ipady=0, padx=0, pady=5, sticky="nsew")
            self.text2.grid(in_=self.tabPage.pages['Logs'].frame, column=8, row=2, columnspan=1, rowspan=1, ipadx=0,
                            ipady=0, padx=0, pady=5, sticky="nsew")
            self.sbar2.grid(in_=self.tabPage.pages['Logs'].frame, column=9, row=2, columnspan=1, rowspan=1, ipadx=0,
                            ipady=0, padx=0, pady=5, sticky="nsew")
            self.entry_1.grid(in_=self.tabPage.pages['Logs'].frame, column=1, row=3, columnspan=7, rowspan=1, ipadx=5,
                              ipady=0, padx=2, pady=0, sticky="ew")
            self.button2.grid(in_=self.tabPage.pages['Logs'].frame, column=8, row=3, columnspan=2, rowspan=1, ipadx=0,
                              ipady=0, padx=5, pady=5, sticky="ew")

            self.tabPage.grid(in_=self.rootM, column=1, row=1, rowspan=3, columnspan=9, ipadx=5, ipady=0, padx=2,
                              pady=0, sticky="nsew")
            self.entry_1.focus()
            self.entry_1.bind('<Return>', (lambda event: self.send()))
            self.tabPage.pages['Logs'].frame.grid_rowconfigure(1, weight=1, minsize=21, pad=0)
            self.tabPage.pages['Logs'].frame.grid_rowconfigure(2, weight=1, minsize=509, pad=0)
            self.tabPage.pages['Logs'].frame.grid_rowconfigure(3, weight=1, minsize=21, pad=0)

            self.tabPage.pages['Logs'].frame.grid_columnconfigure(1, weight=1, minsize=40, pad=0)
            self.tabPage.pages['Logs'].frame.grid_columnconfigure(2, weight=1, minsize=220, pad=0)
            self.tabPage.pages['Logs'].frame.grid_columnconfigure(3, weight=1, minsize=76, pad=2)
            self.tabPage.pages['Logs'].frame.grid_columnconfigure(4, weight=1, minsize=84, pad=0)
            self.tabPage.pages['Logs'].frame.grid_columnconfigure(5, weight=1, minsize=40, pad=0)
            self.tabPage.pages['Logs'].frame.grid_columnconfigure(6, weight=1, minsize=180, pad=0)
            self.tabPage.pages['Logs'].frame.grid_columnconfigure(7, weight=0, minsize=0, pad=0)
            self.tabPage.pages['Logs'].frame.grid_columnconfigure(8, weight=1, minsize=131, pad=0)
            self.tabPage.pages['Logs'].frame.grid_columnconfigure(9, weight=0, minsize=0, pad=0)
            """POI Logs Tab"""
            self.labelp1 = Label(self.tabPage.pages['AddPoi'].frame, bg="#000000", fg="#ff0000", text="AddPoi Logs: ",
                                 justify=LEFT)
            self.textp1 = Text(self.tabPage.pages['AddPoi'].frame, bg="#000000", fg="#ff0000", height=0, width=0, )
            self.labelp1.grid(in_=self.tabPage.pages['AddPoi'].frame, column=1, row=1, columnspan=1, ipadx=0, ipady=0,
                              padx=5, pady=0, rowspan=1, sticky="w")

            self.textp1.grid(in_=self.tabPage.pages['AddPoi'].frame, column=1, row=2, columnspan=1, ipadx=5, ipady=0,
                             padx=2, pady=0, rowspan=2, sticky="news")
            self.tabPage.pages['AddPoi'].frame.grid_rowconfigure(1, weight=0, minsize=15, pad=0)
            self.tabPage.pages['AddPoi'].frame.grid_rowconfigure(2, weight=1, minsize=509, pad=0)
            self.tabPage.pages['AddPoi'].frame.grid_columnconfigure(1, weight=1, minsize=800, pad=0)
            """POI List Tab"""
            self.labelpl1 = Label(self.tabPage.pages['POIList.xml'].frame, bg="#000000", fg="#ff0000",
                                  text="POIList.xml source: ", justify=LEFT)
            self.textpl1 = Text(self.tabPage.pages['POIList.xml'].frame, bg="#000000", fg="#ff0000", height=0,
                                width=0, )
            self.labelpl1.grid(in_=self.tabPage.pages['POIList.xml'].frame, column=1, row=1, columnspan=1, ipadx=0,
                               ipady=0, padx=5, pady=0, rowspan=1, sticky="w")

            self.textpl1.grid(in_=self.tabPage.pages['POIList.xml'].frame, column=1, row=2, columnspan=1, ipadx=5,
                              ipady=0, padx=2, pady=0, rowspan=2, sticky="news")
            self.tabPage.pages['POIList.xml'].frame.grid_rowconfigure(1, weight=0, minsize=15, pad=0)
            self.tabPage.pages['POIList.xml'].frame.grid_rowconfigure(2, weight=1, minsize=509, pad=0)
            self.tabPage.pages['POIList.xml'].frame.grid_columnconfigure(1, weight=1, minsize=800, pad=0)
            """POI Users White List Tab"""
            self.labelwl1 = Label(self.tabPage.pages['WhiteList'].frame, bg="#000000", fg="#ff0000", text="WhiteList: ",
                                  justify=LEFT)
            self.textwl1 = Text(self.tabPage.pages['WhiteList'].frame, bg="#000000", fg="#ff0000", height=0, width=0, )
            self.labelwl1.grid(in_=self.tabPage.pages['WhiteList'].frame, column=1, row=1, columnspan=1, ipadx=0,
                               ipady=0, padx=5, pady=0, rowspan=1, sticky="w")

            self.textwl1.grid(in_=self.tabPage.pages['WhiteList'].frame, column=1, row=2, columnspan=1, ipadx=5,
                              ipady=0, padx=2, pady=0, rowspan=2, sticky="news")
            self.tabPage.pages['WhiteList'].frame.grid_rowconfigure(1, weight=0, minsize=15, pad=0)
            self.tabPage.pages['WhiteList'].frame.grid_rowconfigure(2, weight=1, minsize=509, pad=0)
            self.tabPage.pages['WhiteList'].frame.grid_columnconfigure(1, weight=1, minsize=800, pad=0)
            """HTTP Server Tab"""
            self.labelhl1 = Label(self.tabPage.pages['HTTP_Server'].frame, bg="#000000", fg="#ff0000",
                                  text="HTTP server Logs: ", justify=LEFT)
            self.texthl1 = Text(self.tabPage.pages['HTTP_Server'].frame, bg="#000000", fg="#ff0000", height=0,
                                width=0, )
            self.labelhl1.grid(in_=self.tabPage.pages['HTTP_Server'].frame, column=1, row=1, columnspan=1, ipadx=0,
                               ipady=0, padx=5, pady=0, rowspan=1, sticky="w")
            self.buttonh2 = Button(self.tabPage.pages['HTTP_Server'].frame, text="Start HTTP Server",
                                   command=self.star_https)
            self.buttonh2.grid(in_=self.tabPage.pages['HTTP_Server'].frame, column=2, row=1, columnspan=2, rowspan=1,
                               ipadx=0, ipady=0, padx=5, pady=5, sticky="ew")
            self.buttonh3 = Button(self.tabPage.pages['HTTP_Server'].frame, text="Shutdown HTTP Server",
                                   command=self.shutdHTTPS)
            self.buttonh3.grid(in_=self.tabPage.pages['HTTP_Server'].frame, column=2, row=3, columnspan=2, rowspan=1,
                               ipadx=0, ipady=0, padx=5, pady=5, sticky="ew")
            self.entryP1 = Entry(self.tabPage.pages['HTTP_Server'].frame, textvariable=strsp1, justify="center",
                                 relief="flat", width=0, )
            self.entryP1.grid(in_=self.tabPage.pages['HTTP_Server'].frame, column=2, row=2, columnspan=1, ipadx=0,
                              ipady=0, padx=5, pady=5, rowspan=1, sticky="ew")
            self.entryP2 = Entry(self.tabPage.pages['HTTP_Server'].frame, textvariable=strsp2, justify="center",
                                 relief="flat", width=0, )
            self.entryP2.grid(in_=self.tabPage.pages['HTTP_Server'].frame, column=3, row=2, columnspan=1, ipadx=0,
                              ipady=0, padx=5, pady=5, rowspan=1, sticky="ew")

            self.texthl1.grid(in_=self.tabPage.pages['HTTP_Server'].frame, column=1, row=2, columnspan=1, ipadx=5,
                              ipady=0, padx=2, pady=0, rowspan=4, sticky="news")
            self.tabPage.pages['HTTP_Server'].frame.grid_rowconfigure(1, weight=0, minsize=15, pad=0)
            self.tabPage.pages['HTTP_Server'].frame.grid_rowconfigure(2, weight=0, minsize=20, pad=0)
            self.tabPage.pages['HTTP_Server'].frame.grid_rowconfigure(3, weight=0, minsize=20, pad=0)
            self.tabPage.pages['HTTP_Server'].frame.grid_rowconfigure(4, weight=1, minsize=469, pad=0)

            self.tabPage.pages['HTTP_Server'].frame.grid_columnconfigure(1, weight=1, minsize=800, pad=0)
            self.tabPage.pages['HTTP_Server'].frame.grid_columnconfigure(2, weight=0, minsize=40, pad=0)

            """POIKeystones Locations Tab"""
            self.labelk1 = Label(self.tabPage.pages['Keystones Locations'].frame, bg="#000000", fg="#ff0000",
                                 text="Keystones Locations: ", justify=LEFT)
            self.textk1 = Text(self.tabPage.pages['Keystones Locations'].frame, bg="#000000", fg="#ff0000", height=0,
                               width=0, )
            self.labelk1.grid(in_=self.tabPage.pages['Keystones Locations'].frame, column=1, row=1, columnspan=1,
                              ipadx=0, ipady=0, padx=5, pady=0, rowspan=1, sticky="w")

            self.textk1.grid(in_=self.tabPage.pages['Keystones Locations'].frame, column=1, row=2, columnspan=1,
                             ipadx=5, ipady=0, padx=2, pady=0, rowspan=2, sticky="news")
            self.buttonk3 = Button(self.tabPage.pages['Keystones Locations'].frame, text="Keystones locations",
                                   command=self.readKL)
            self.buttonk3.grid(in_=self.tabPage.pages['Keystones Locations'].frame, column=2, row=1, columnspan=1,
                               rowspan=1, ipadx=0, ipady=0, padx=5, pady=5, sticky="ew")

            self.tabPage.pages['Keystones Locations'].frame.grid_rowconfigure(1, weight=0, minsize=15, pad=0)
            self.tabPage.pages['Keystones Locations'].frame.grid_rowconfigure(2, weight=1, minsize=509, pad=0)
            self.tabPage.pages['Keystones Locations'].frame.grid_columnconfigure(1, weight=1, minsize=760, pad=0)
            self.tabPage.pages['Keystones Locations'].frame.grid_columnconfigure(2, weight=1, minsize=40, pad=0)
            """POIKeystones Locations Tab"""
            self.labelf1 = Label(self.tabPage.pages['FTP Client'].frame, bg="#000000", fg="#ff0000",
                                 text="FTP Client Logs: ", justify=LEFT)
            self.textf1 = Text(self.tabPage.pages['FTP Client'].frame, bg="#000000", fg="#ff0000", height=0, width=0, )
            self.labelf1.grid(in_=self.tabPage.pages['FTP Client'].frame, column=1, row=1, columnspan=1, ipadx=0,
                              ipady=0, padx=5, pady=0, rowspan=1, sticky="w")

            self.textf1.grid(in_=self.tabPage.pages['FTP Client'].frame, column=1, row=2, columnspan=1, ipadx=5,
                             ipady=0, padx=2, pady=0, rowspan=2, sticky="news")
            self.buttonf3 = Button(self.tabPage.pages['FTP Client'].frame, text="FTP Client", command=self.startFtp)
            self.buttonf3.grid(in_=self.tabPage.pages['FTP Client'].frame, column=2, row=1, columnspan=1, rowspan=1,
                               ipadx=0, ipady=0, padx=5, pady=5, sticky="ew")

            self.tabPage.pages['FTP Client'].frame.grid_rowconfigure(1, weight=0, minsize=15, pad=0)
            self.tabPage.pages['FTP Client'].frame.grid_rowconfigure(2, weight=1, minsize=509, pad=0)
            self.tabPage.pages['FTP Client'].frame.grid_columnconfigure(1, weight=1, minsize=760, pad=0)
            self.tabPage.pages['FTP Client'].frame.grid_columnconfigure(2, weight=1, minsize=40, pad=0)
            self.rootM.grid_columnconfigure(1, weight=1, minsize=200, pad=0)
            self.rootM.grid_rowconfigure(1, weight=1, minsize=200, pad=0)

            self.read_white_list(self.parent.parent.settings['wLPath'])
            # self.th_R.parent.readpoi(self.parent.parent.settings['poiPath'])
            self.textk1.focus()
            # self.readKL()
            self.rootM.mainloop()

        def startFtp(self):
            th_f = self.parent.KFPFTP(self)
            th_f.start()
            # th_f.join()

        def update_poi_list(self, value):
            self.textpl1.config(state=NORMAL)
            self.textpl1.delete(1.0, END)
            self.textpl1.insert(END, value + '\n' + '</poilist>')
            self.textpl1.config(state=DISABLED)
            self.textpl1.see(END)

        def update_keystones_list(self, value):
            self.textk1.config(state=NORMAL)
            self.textk1.insert('end', time.strftime("%X") + " - " + value + '\n')
            self.textk1.config(state=DISABLED)
            self.textk1.see(END)

        def update(self, value):
            if 'INF' in value:
                s = value[value.find(' INF ') + 5:]
            else:
                s = value
            self.text1.config(state=NORMAL)
            self.text1.insert('end', time.strftime("%X") + " - " + s + '\n')
            self.text1.config(state=DISABLED)
            self.text1.see(END)

        def updateFTP(self, value):
            self.textf1.config(state=NORMAL)
            self.textf1.insert('end', time.strftime("%X") + " - " + value + '\n')
            self.textf1.config(state=DISABLED)
            self.textf1.see(END)

        def updateHTTP(self, value):
            self.texthl1.config(state=NORMAL)
            self.texthl1.insert('end', time.strftime("%X") + " - " + value + '\n')
            self.texthl1.config(state=DISABLED)
            self.texthl1.see(END)

        def updatePoi(self, value):
            self.textp1.config(state=NORMAL)
            self.textp1.insert('end', time.strftime("%c") + " - " + value + '\n')
            self.textp1.config(state=DISABLED)
            self.textp1.see(END)

        def readKL(self):
            print 'oooo'
            th_kl = self.parent.ShowKeyLocation(self, None)
            th_kl.start()
            th_kl.join()

        def listUsers(self, users_list):
            self.text2.delete(1.0, END)
            for user in users_list:
                self.text2.insert(END, user + '\n')

        def send(self):
            if self.entry_1.get()[:2] == 'th':
                self.update('Thread actif: ' + str(threading.active_count()))
                for th in threading.enumerate():
                    self.update(str(th))
            elif self.entry_1.get()[:12] == 'add poiuser ':  # TODO
                print 'add ' + self.entry_1.get()[12:]
                s = self.entry_1.get()[12:]
                s1 = s.split(' ')
                for s2 in s1:
                    print s2
            elif self.entry_1.get()[:2] == 'SK':  # TODO
                th_kl = self.parent.ShowKeyLocation(self, None)
                th_kl.start()
            else:
                print self.entry_1.get()
                self.sendAllData(self.entry_1.get())

        def sendAllData(self, value):
            self.sock.sendall(value + '\n')

        def send_fin(self):
            self.button1.configure(text="Connect", command=self.connect)
            self.button2.configure(state='disable')
            self.sock.send('exit\n')
            self.th_R.exite()
            self.sock.close()
            self.th_R.join()

        def read_white_list(self, x):
            try:
                with open(x, "r") as f:
                    s = ''.join(f.readlines())
                    self.textwl1.config(state=NORMAL)
                    self.textwl1.delete(1.0, END)
                    self.textwl1.insert(END, s)
                    self.textwl1.config(state=DISABLED)
                    self.textwl1.see(END)
                    return s
            except IOError as e:
                self.textwl1.config(state=NORMAL)
                self.textwl1.delete(1.0, END)
                self.textwl1.insert(END, str(e))
                self.textwl1.config(state=DISABLED)
                self.textwl1.see(END)

        def star_https(self):
            self.th_Http = self.parent.httpServer(self)
            self.th_Http.start()

        def shutdHTTPS(self):
            self.th_Http.join()

        def connect(self):
            self.button1.configure(text='Disconnect', command=self.send_fin)
            self.button2.configure(state='normal')
            self.update('Connecting to ' + self.parent.settings['telnet_server'])
            sadress = (self.entry4.get(), int(self.entry2.get()))
            self.sock.connect(sadress)
            self.update(u'Connexion établie avec le serveur.')
            self.th_R.start()

        def refresh_players_list(self):
            t = Timer(59.0, self.refresh_players_list)
            t.start()
            self.sock.send('lp\n')

    class Send_data(threading.Thread):
        def __init__(self, sock, value):
            threading.Thread.__init__(self)
            self.sock = sock
            self.value = value

        def run(self):
            try:
                print self.value
                self.sock.send(self.value + '\n')
            except Exception as e:
                print e

    class getNameBySid(threading.Thread):
        def __init__(self, parent, value):
            threading.Thread.__init__(self)
            self.sId = value
            self.parent = parent

        def run(self):
            t = ET.parse('./xml/PlayersList2.xml')
            r = t.getroot()
            found = False
            for player in r.findall('player'):
                try:
                    steamid = player.get('steamId')
                    if steamid == self.sId:
                        found = True
                        self.parent.parent.update_keystones_list(
                            "SteamId: " + steamid + " - Username: " + player.get('name'))
                except Exception as e:
                    print e
            if not found:
                self.parent.parent.update_keystones_list("SteamId: " + self.sId + " - Username: unknow")

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
