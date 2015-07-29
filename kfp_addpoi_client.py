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
 
from Tkinter import *
import getopt
import os
import re
import signal
import socket
import sys
import sys
import sys
from threading import Thread
import threading
import time

from TabPages import *
import xml.etree.ElementTree as ET

class KFP_AddPOI(threading.Thread):
    def usage(self):
        print "This program extract and merge map tiles of all players.Then write it in a folder with verious zoom" \
              " levels. In order to hide player bases, this program keep only the oldest version of each tile by default." \
              " By providing the Server telnet address and password this software run in background and is able to do the" \
              " following features:\n" \
              " - Update tiles when a player disconnect\n" \
              " - Add Poi when a user say /addpoi title\n" \
              " - Update players csv coordinates file\n"
        print "Usage:"
        print "map_reader -g XX [options]"
        print " -g \"C:\\Users..\":\t The folder that contain .map files"
        print " -t \"tiles\":\t\t The folder that will contain tiles (Optional)"
        print " -z 8:\t\t\t\t Zoom level 4-n. Number of tiles to extract around position 0,0 of map." \
              " It is in the form of 4^n tiles.It will extract a grid of 2^n*16 tiles on each side.(Optional)"
        print " -s telnethost:port \t7DTD server ip and port (telnet port, default 8081) (Optional)"
        print " -p CHANGEME Password of telnet, default is CHANGEME (Optional)"
        print " --ignore-poi \t Do not read /addpoi command of players"
        print " --ignore-track \t Do not write players track in csv files"
        print " -newest Keep track of updates and write the last version of tiles. This will show players bases on map. " \
              "(Optional)"

    def __init__(self,parent):
        threading.Thread.__init__(self)
        global sAddress, sip, sPort, sPass, wLPath, poiPath, verbose, settings, fen
        sIp = 'localhost'
        sPort = 8081
        self.parent = parent
        print 'ini'
        print 'jjj'
        sPass = None
        sIp = None
        sPort = None
        wLPath = None
        poiPath = None
        alwd = False
        adp = False
        verbose = None
        psdR = None
        poiName = None
        settings = {}
        try:
            f = open('./config.kfp', "r")
            for i in f:
                i = i.strip()
                if len(i) > 0:
                    s = i.split("=")
                    key = s[0].strip()
                    value = s[1].strip()
                    settings[key] = value
        except:
            print("ERROR: file '" + config_file + "' does not exist or is improperly formatted")
           
        print settings['sIp']
        """try:
            for opt, value in getopt.getopt(sys.argv[1:], "i:p:z:w:k:v")[0]:
                if opt == "-i":
                    settings['sIp'] = value
                elif opt == "-p":
                    settings['sPort'] = int(value)
                elif opt == "-z":
                    settings['sPass'] = value
                elif opt == "-w":
                    settings['wLPath'] = value
                elif opt == "-k":
                    settings['poiPath'] = value
                elif opt == "-v":
                    settings['verbose'] = value
                print 'opt: ' + value
        except getopt.error, msg:
            print 'error'
            self.usage()
            raw_input()
            exit(-1)"""

        if settings['wLPath'] is None:  # Show gui to select poi whitelist folder
            settings['wLPath'] = self.selFile({"initialdir": os.path.expanduser("~\\Documents\\7 Days To Die\\Saves\\Random Gen\\"),
                                               "title": "Choose the Whiteliste that contain autorised users infos."})

        if len(settings['wLPath']) == 0:
            print "You must define the leaflet users whitelist."
            exit(-1)

        if settings['poiPath'] is None:  # Show gui to select poi list.xml path
            settings['poiPath'] = self.selFile({"initialdir": os.path.expanduser("~\\Documents\\7 Days To Die\\Saves\\Random Gen\\"),
                        "title": "Choose the POIList.xml path."})

        if len(settings['poiPath']) == 0:
            print "You must define the leaflet poi list."
            exit(-1)
            
        sAddress = (settings['sIp'], int(settings['sPort']))
        fen = self.AddPOI_GUI(self)
        print 'fen start'
        fen.start()

   
    class ThreadReception(threading.Thread):
        def __init__(self, conn, fen):
            threading.Thread.__init__(self)
            self.sock = conn  # réf. du socket de connexion
            self.a = fen
            self.exiter = False
            
        def exite(self):
            if not self.exiter:
                self.exiter = True
        def writePoi(self, x, psdR, sid, poiName, loc):
             try:
                 old = self.readPoi(x)
                 with open(x, "w") as f:
                     f.write(old + '\n<poi sname=\"' + psdR + '\" steamId=\"' + sid + '\" pname=\"' + poiName + '\" pos=\"' + loc[0] + ',0,' + loc[2] + '\" icon=\"farm\" />\n</poilist>')
                 old = self.readPoi(x)   
                 return True
                 
                
             except IOError:
                 return False

        def readPoi(self, x):
             try:
                 print x
                 with open(x, "r") as f:
                     s = ''.join(f.readlines()[:-1])[:-1]
                     if len(s) <= 0:
                         s = '<poilist>\n'
                     self.a.updatePOIList(s)
                     return s
             except IOError:
                 print "error"


        def addPoi(self, x, psdR, sid, poiName, loc, sock):
             try:
                 if self.writePoi(x, psdR, sid, poiName, loc):
                     self.a.updatePoi('Poi \"' + poiName + '\" added by ' + psdR)
                     self.a.sendAllData('say \"[00FF00]' + psdR + ', Poi Name: ' + poiName + ' added successfully.\"\n')
                 else:
                     self.a.updatePoi('Poi \"' + poiName + '\" non added. Error... Requested by ' + psdR)
                     self.a.sendAllData('say \"[00FF00]' + psdR + ', error during reading or writing data. Contact an admin.\"\n')
             except IOError:
                 print "error"        
            
        def run(self):
            sPass = settings['sPass']
            sIp = settings['sIp']
            sPort = settings['sPort']
            wLPath = str(settings['wLPath'])
            alwd = False
            adp = False
            verbose = bool(settings['verbose'])
            psdR = None
            poiName = None
            poiPath = settings['poiPath']
            listUsers = []
            print 'okik'
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
                        self.a.update('Connected...\nSending password...')
                        self.a.sendAllData(sPass)
                    else:
                        for s in s2:
                             print s
                             if len(s) >= 5:
                                 nn = 'Player disconnected: EntityID='
                                 nn2 = ', PlayerID=\''
                                 if nn in s:
                                     steamID = s[s.find(nn2)+len(nn2):s.find('\', OwnerID=\'')]
                                     print steamID                                     
                                 if 'Logon successful.' in d and not loged:
                                     loged = True
                                     mp = self.a.parent.mapR(self.a.parent,'76561198009609645')  
                                     mp.start()         
                                     print >> sys.stderr, 'Logon successful...'
                                                                  
                                     self.a.sendAllData('lp')
                                 elif verbose:                                 
                                     self.a.update(s)
                                 if 'GMSG:' in s:  # chat msg
                                     psdRTp = s[s.find('GMSG:') + 6:]
                                     tfd = [' joined the game', ' left the game', ' killed player']
                                     skip = False
                                     for ik in range(0, len(tfd)):
                                         if tfd[ik] in s:
                                             psdRCt = psdRTp[:psdRTp.find(tfd[ik])]
                                             print tfd[ik]
                                             if ik == 1:
                                                 print ik
                                                 
                                                 skip = True
                                     if skip:
                                         print ''  # TODO gen current user tiles if deco
                                     elif ap in s:
                                         adp = True
                                         self.a.sendAllData('lp')
                                         psdRPOI = psdRTp[:psdRTp.find(': ')]                                    
                                         poiName = s[s.find(ap) + len(ap):]
                                         if re.search(r'^[A-Za-z0-9Ü-ü_ \-]{3,25}$', poiName):
                                             self.a.updatePoi('Adding a POI is requested by ' + psdRPOI + ".")
                                             psdR = psdRPOI
                                         else:
                                             self.a.updatePoi('Bad Poi name requested by ' + psdRPOI)
                                             self.a.sendAllData('say \"[FF0000]' + psdRPOI + ', The Poi Name must contain between 3 and 25 alphanumerics characters .\"')
                                 elif ". id=" in s:
                                     sid = ""
                                     fg = s[:s.find('. id=')]
                                     i = s.find(', ')
                                     j = s.find(', pos=(')
                                     psd = s[i + 2:j]
                                     if psd in listUsers:
                                         listUsers.remove(psd)
                                     listUsers.insert(int(fg), psd)                                
                                     self.a.listUsers(listUsers)
                                     gId = s[s.find('. id=') + 5:i]
                                     l = s.find('steamid=')
                                     sid = s[l + 8:s.find(',', l)]
                                     locTp = s[j + 7:]
                                     loc = locTp[:locTp.find('), rot')].split(', ')
                                     if adp:
                                         if psdR == psd and not psdR == None:
                                             adp = False
                                             t = ET.parse(wLPath)
                                             r = t.getroot()
                                             for u in r.findall('user'):
                                                 if u.get('steamId') == sid and u.get('rank') >= '1' and u.get('allowed') == '1':
                                                     self.addPoi(poiPath, psdR, sid, poiName, loc, sock)
                                                 else:
                                                     self.a.updatePoi('Bad user \"' + psdR + '\" steamId: ' + sid)
                                                     self.a.sendAllData('say \"[FF0000]' + psdRPOI + ', your are not allowed to add a poi.\"')
                                                                 
                                     
            print u"Client arrêté. connexion interrompue."
            self.sock.close()
    """ HTTP SERVER """       
    class httpServer(threading.Thread):
        """ Class describing a simple HTTP server objects."""
       
        def __init__(self, gui):
             """ Constructor """
             threading.Thread.__init__(self)
             self.GUI = gui   
             self.host = ''
             self.port = 8084         
             self.www = '.'  # Directory where webpage files are stored
      
        def run(self):
             """ Attempts to aquire the socket and launch the server """ 
             self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
             try: 
                 self.GUI.updateHTTP("Launching HTTP server on " + self.host + ":" + str(self.port))
                 self.socket.bind((self.host, self.port))             
             except Exception as e:            
                 ub = False             
                 while not ub:
                     self.GUI.updateHTTP("Warning: Could not aquite port: " + str(self.port) + "\n")
                     self.GUI.updateHTTP("I will try a higher port")
                     self.port = self.port + 1
                     try:
                         self.GUI.updateHTTP("Launching HTTP server on " + self.host + ":" + str(self.port))
                         self.socket.bind((self.host, self.port))
                         ub = True
                     except Exception as e:
                         self.GUI.updateHTTP("ERROR: Failed to acquire sockets for ports " + str(self.port))

                    
             self.GUI.updateHTTP("Server successfully acquired the socket with port: " + str(self.port))
             self.GUI.updateHTTP("Press Ctrl+C to shut down the server and exit.")
             self._wait_for_connections()
          
        def shutdown(self):   
             """ Shut down the server """
             try:
                 self.GUI.updateHTTP("Shutting down the server")
                 self.socket.shutdown(socket.SHUT_RDWR)
                 
             except Exception as e:
                 self.GUI.updateHTTP("Warning: could not shut down the socket. Maybe it was already closed? " + str(e))
          
             
        def _gen_headers(self, code):
             """ Generates HTTP response Headers. Ommits the first line! """         
             # determine response code
             h = ''
             if (code == 200):
                h = 'HTTP/1.1 200 OK\n'
             elif(code == 404):
                h = 'HTTP/1.1 404 Not Found\n'         
             # write further headers
             current_date = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime()) 
             h += 'Date: ' + current_date + '\n'
             h += 'Server: KFP-Python-HTTP-Server\n'
             h += 'Connection: close\n\n'  # signal that the conection wil be closed after complting the request
             return h

        def _wait_for_connections(self):
             """ Main loop awaiting connections """
             while True:
                 self.GUI.updateHTTP("Awaiting New connection")
                 self.socket.listen(3)  # maximum number of queued connections
                 
                 conn, addr = self.socket.accept()
                 # conn - socket to client
                 # addr - clients address
                 
                
                 
                 data = conn.recv(1024)  # receive data from client
                 string = bytes.decode(data)  # decode it to string
                 
                 # determine request method  (HEAD and GET are supported)
                 request_method = string.split(' ')[0]
                 self.GUI.updateHTTP("Got connection from:" + str(addr) + " - Method: " + request_method)
                 self.GUI.updateHTTP("Request body: " + string.split('\n')[0])
                 
                 # if string[0:3] == 'GET':
                 if (request_method == 'GET') | (request_method == 'HEAD'):
                     # file_requested = string[4:]

                     # split on space "GET /file.html" -into-> ('GET','file.html',...)
                     file_requested = string.split(' ')
                     file_requested = file_requested[1]  # get 2nd element
            
                     # Check for URL arguments. Disregard them
                     file_requested = file_requested.split('?')[0]  # disregard anything after '?'
             
                     if (file_requested == '/'):  # in case no file is specified by the browser
                         file_requested = '/index.html'  # load index.html by default
                     

                     file_requested = self.www + file_requested
                     self.GUI.updateHTTP("Serving web page [" + file_requested + "]")

                     # # Load file content
                     try:
                         file_handler = open(file_requested, 'rb')
                         if (request_method == 'GET'):  # only read the file when GET
                             response_content = file_handler.read()  # read file content                       
                         file_handler.close()
                         
                         response_headers = self._gen_headers(200)          
                         
                     except Exception as e:  # in case file was not found, generate 404 page
                         self.GUI.updateHTTP("Warning, file not found. Serving response code 404\n" + str(e))
                         response_headers = self._gen_headers(404)
                     
                         if (request_method == 'GET'):
                            response_content = b"<html><head>" + \
                                    "<meta http-equiv=\"Content-Type\" content=\"text/html; charset=utf-8\">"+ \
                                    "</head><body style=\"background-image:url(404.gif);"+ \
                                    "background-repeat:no-repeat; background-position:center center;"+ \
                                    "color: red;"+ \
                                    "background-color:black;\"><h2>KFP ZBot Lite Simple Web Server</h2>"+ \
                                    "<!--div>404 - Not Found</div--></body></html>"  
                         

                     server_response = response_headers.encode()  # return headers for GET and HEAD
                     if (request_method == 'GET'):
                         server_response += response_content  # return additional conten for GET only


                     conn.send(server_response)
                     self.GUI.updateHTTP("Closing connection with client")
                     conn.close()

                 else:
                     self.GUI.updateHTTP("Unknown HTTP request method: " + request_method)
          


        def graceful_shutdown(sig, dummy):
            """ This function shuts down the server. It's triggered
            by SIGINT signal """
            s.shutdown()  # shut down the server
            import sys
            sys.exit(1)
                
                
        def keerunning(self, value):
            self.keep_running = bool(value)
        
    class AddPOI_GUI(threading.Thread):    
        def __init__(self, parent):        
            threading.Thread.__init__(self)        
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)        
            self.parent = parent
            self.th_R = self.parent.ThreadReception(self.sock, self)
            self.rootM = Tk()
            self.rootM.configure(bg='black')
            self.rootM.title = "ZBot lite py"
            self.tabPage = TabbedPageSet(self.rootM, page_names=['Logs', 'AddPoi', 'POIList.xml', 'WhiteList', 'HTTP_Server'], bg="#000000", n_rows=0, expand_tabs=True,)
            self.tabPage.pages['Logs'].frame.configure(bg="#000000")
            self.tabPage.pages['AddPoi'].frame.configure(bg="#000000")
            self.tabPage.pages['POIList.xml'].frame.configure(bg="#000000")
            self.tabPage.pages['WhiteList'].frame.configure(bg="#000000")
            self.tabPage.pages['HTTP_Server'].frame.configure(bg="#000000")
            self.label1 = Label(self.tabPage.pages['Logs'].frame, bg="#000000", fg="#ff0000", borderwidth=1, text="Server IP: ",)
            self.label2 = Label(self.tabPage.pages['Logs'].frame, bg="#000000", fg="#ff0000", text="Server Port: ",)
            self.label3 = Label(self.tabPage.pages['Logs'].frame, bg="#000000", fg="#ff0000", text="Server Password:",)
            strs1 = StringVar()
            strs2 = StringVar()
            strs3 = StringVar()
            strs4 = StringVar()        
            strs1.set(settings['sPort'])
            strs2.set(settings['sIp'])
            strs3.set(settings['sPass'])
            strs4.set("say ")
            self.entry_1 = Entry(self.tabPage.pages['Logs'].frame, textvariable=strs4, bg="#000000", fg="#ff0000", width=0,)
            self.entry2 = Entry(self.tabPage.pages['Logs'].frame, textvariable=strs1, justify="center", relief="flat", width=0,)
            self.entry3 = Entry(self.tabPage.pages['Logs'].frame, textvariable=strs3, justify="center", relief="flat", width=0, show="*")
            self.button1 = Button(self.tabPage.pages['Logs'].frame, text="Connect", command=self.connect)
            self.button2 = Button(self.tabPage.pages['Logs'].frame, text="Send", command=self.send)
            
            self.sbar1 = Scrollbar(self.tabPage.pages['Logs'].frame)
            self.sbar2 = Scrollbar(self.tabPage.pages['Logs'].frame)
            
            self.text1 = Text(self.tabPage.pages['Logs'].frame, bg="#000000", fg="#ff0000", height=0, width=0,)        
            self.text2 = Text(self.tabPage.pages['Logs'].frame, bg="#000000", fg="#ff0000", height=0, width=0,)
            self.text3 = Text(self.tabPage.pages['Logs'].frame, bg="#000000", fg="#ff0000", height=0, width=0,)
            
            self.entry4 = Entry(self.tabPage.pages['Logs'].frame, textvariable=strs2, justify="center", relief="flat", width=0,)
            self.sbar1.config(command=self.text1.yview)
            self.sbar1.config(command=self.text2.yview)
            
            self.label1.grid(in_=self.tabPage.pages['Logs'].frame, column=1, row=1, columnspan=1, ipadx=0, ipady=0, padx=5, pady=5, rowspan=1, sticky="")
            self.entry4.grid(in_=self.tabPage.pages['Logs'].frame, column=2, row=1, columnspan=1, ipadx=0, ipady=0, padx=5, pady=5, rowspan=1, sticky="ew")
            self.label2.grid(in_=self.tabPage.pages['Logs'].frame, column=3, row=1, columnspan=1, ipadx=0, ipady=0, padx=5, pady=5, rowspan=1, sticky="")
            self.entry2.grid(in_=self.tabPage.pages['Logs'].frame, column=4, row=1, columnspan=1, ipadx=0, ipady=0, padx=5, pady=5, rowspan=1, sticky="ew")
            self.label3.grid(in_=self.tabPage.pages['Logs'].frame, column=5, row=1, columnspan=1, ipadx=0, ipady=0, padx=5, pady=5, rowspan=1, sticky="")
            self.entry3.grid(in_=self.tabPage.pages['Logs'].frame, column=6, row=1, columnspan=1, ipadx=0, ipady=0, padx=5, pady=5, rowspan=1, sticky="ew")
            self.button1.grid(in_=self.tabPage.pages['Logs'].frame, column=8, row=1, columnspan=2, ipadx=0, ipady=0, padx=5, pady=5, rowspan=1, sticky="nsew")
            self.text1.grid(in_=self.tabPage.pages['Logs'].frame, column=1, row=2, columnspan=6, rowspan=1, ipadx=5, ipady=0, padx=2, pady=5, sticky="news")        
            self.sbar1.grid(in_=self.tabPage.pages['Logs'].frame, column=7, row=2, columnspan=1, rowspan=1, ipadx=0, ipady=0, padx=0, pady=5, sticky="nsew")
            self.text2.grid(in_=self.tabPage.pages['Logs'].frame, column=8, row=2, columnspan=1, rowspan=1, ipadx=0, ipady=0, padx=0, pady=5, sticky="nsew")
            self.sbar2.grid(in_=self.tabPage.pages['Logs'].frame, column=9, row=2, columnspan=1, rowspan=1, ipadx=0, ipady=0, padx=0, pady=5, sticky="nsew")
            self.entry_1.grid(in_=self.tabPage.pages['Logs'].frame, column=1, row=3, columnspan=7, rowspan=1, ipadx=5, ipady=0, padx=2, pady=0, sticky="ew")
            self.button2.grid(in_=self.tabPage.pages['Logs'].frame, column=8, row=3, columnspan=2, rowspan=1, ipadx=0, ipady=0, padx=5, pady=5, sticky="ew")
            
            self.tabPage.grid(in_=self.rootM, column=1, row=1, rowspan=3, columnspan=9, ipadx=5, ipady=0, padx=2, pady=0, sticky="nsew")
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

            self.labelp1 = Label(self.tabPage.pages['AddPoi'].frame, bg="#000000", fg="#ff0000", text="AddPoi Logs: ", justify=LEFT)
            self.textp1 = Text(self.tabPage.pages['AddPoi'].frame, bg="#000000", fg="#ff0000", height=0, width=0,)        
            self.labelp1.grid(in_=self.tabPage.pages['AddPoi'].frame, column=1, row=1, columnspan=1, ipadx=0, ipady=0, padx=5, pady=0, rowspan=1, sticky="w")
            
            self.textp1.grid(in_=self.tabPage.pages['AddPoi'].frame, column=1, row=2, columnspan=1, ipadx=5, ipady=0, padx=2, pady=0, rowspan=2, sticky="news")
            self.tabPage.pages['AddPoi'].frame.grid_rowconfigure(1, weight=0, minsize=15, pad=0)
            self.tabPage.pages['AddPoi'].frame.grid_rowconfigure(2, weight=1, minsize=509, pad=0)
            self.tabPage.pages['AddPoi'].frame.grid_columnconfigure(1, weight=1, minsize=800, pad=0)
            
            self.labelpl1 = Label(self.tabPage.pages['POIList.xml'].frame, bg="#000000", fg="#ff0000", text="POIList.xml source: ", justify=LEFT)
            self.textpl1 = Text(self.tabPage.pages['POIList.xml'].frame, bg="#000000", fg="#ff0000", height=0, width=0,)        
            self.labelpl1.grid(in_=self.tabPage.pages['POIList.xml'].frame, column=1, row=1, columnspan=1, ipadx=0, ipady=0, padx=5, pady=0, rowspan=1, sticky="w")
            
            self.textpl1.grid(in_=self.tabPage.pages['POIList.xml'].frame, column=1, row=2, columnspan=1, ipadx=5, ipady=0, padx=2, pady=0, rowspan=2, sticky="news")
            self.tabPage.pages['POIList.xml'].frame.grid_rowconfigure(1, weight=0, minsize=15, pad=0)
            self.tabPage.pages['POIList.xml'].frame.grid_rowconfigure(2, weight=1, minsize=509, pad=0)
            self.tabPage.pages['POIList.xml'].frame.grid_columnconfigure(1, weight=1, minsize=800, pad=0)

            self.labelwl1 = Label(self.tabPage.pages['WhiteList'].frame, bg="#000000", fg="#ff0000", text="WhiteList: ", justify=LEFT)
            self.textwl1 = Text(self.tabPage.pages['WhiteList'].frame, bg="#000000", fg="#ff0000", height=0, width=0,)        
            self.labelwl1.grid(in_=self.tabPage.pages['WhiteList'].frame, column=1, row=1, columnspan=1, ipadx=0, ipady=0, padx=5, pady=0, rowspan=1, sticky="w")
            
            self.textwl1.grid(in_=self.tabPage.pages['WhiteList'].frame, column=1, row=2, columnspan=1, ipadx=5, ipady=0, padx=2, pady=0, rowspan=2, sticky="news")
            self.tabPage.pages['WhiteList'].frame.grid_rowconfigure(1, weight=0, minsize=15, pad=0)
            self.tabPage.pages['WhiteList'].frame.grid_rowconfigure(2, weight=1, minsize=509, pad=0)
            self.tabPage.pages['WhiteList'].frame.grid_columnconfigure(1, weight=1, minsize=800, pad=0)

            self.labelhl1 = Label(self.tabPage.pages['HTTP_Server'].frame, bg="#000000", fg="#ff0000", text="WhiteList: ", justify=LEFT)
            self.texthl1 = Text(self.tabPage.pages['HTTP_Server'].frame, bg="#000000", fg="#ff0000", height=0, width=0,)        
            self.labelhl1.grid(in_=self.tabPage.pages['HTTP_Server'].frame, column=1, row=1, columnspan=1, ipadx=0, ipady=0, padx=5, pady=0, rowspan=1, sticky="w")
            self.buttonh2 = Button(self.tabPage.pages['HTTP_Server'].frame, text="Start HTTP Server", command=self.startHTTPS)        
            self.buttonh2.grid(in_=self.tabPage.pages['HTTP_Server'].frame, column=2, row=1, columnspan=1, rowspan=1, ipadx=0, ipady=0, padx=5, pady=5, sticky="ew")
            self.buttonh3 = Button(self.tabPage.pages['HTTP_Server'].frame, text="Shutdown HTTP Server", command=self.shutdHTTPS)        
            self.buttonh3.grid(in_=self.tabPage.pages['HTTP_Server'].frame, column=2, row=2, columnspan=1, rowspan=1, ipadx=0, ipady=0, padx=5, pady=5, sticky="ew")
            
            self.texthl1.grid(in_=self.tabPage.pages['HTTP_Server'].frame, column=1, row=2, columnspan=1, ipadx=5, ipady=0, padx=2, pady=0, rowspan=2, sticky="news")
            self.tabPage.pages['HTTP_Server'].frame.grid_rowconfigure(1, weight=0, minsize=15, pad=0)
            self.tabPage.pages['HTTP_Server'].frame.grid_rowconfigure(2, weight=1, minsize=509, pad=0)
            
            self.tabPage.pages['HTTP_Server'].frame.grid_columnconfigure(1, weight=1, minsize=800, pad=0)
            self.tabPage.pages['HTTP_Server'].frame.grid_columnconfigure(2, weight=0, minsize=40, pad=0)
            self.rootM.grid_columnconfigure(1, weight=1, minsize=200, pad=0)
            self.rootM.grid_rowconfigure(1, weight=1, minsize=200, pad=0)
            print settings['wLPath'] 
            self.readWL(settings['wLPath'])
            self.th_R.readPoi(settings['poiPath'])
            
            self.rootM.mainloop();
            
        def updatePOIList(self, value):
            self.textpl1.config(state=NORMAL)
            self.textpl1.delete(1.0, END)
            self.textpl1.insert(END, value + '\n' + '</poilist>')
            self.textpl1.config(state=DISABLED)
            self.textpl1.see(END)
            
        def update(self, value):
            if 'INF' in value:
                s = value[value.find(' INF ') + 5:]
            else:
                s = value
            self.text1.config(state=NORMAL)
            self.text1.insert('end', time.strftime("%X") + " - " + s + '\n')
            self.text1.config(state=DISABLED)
            self.text1.see(END)
            
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
            
        def listUsers(self, usersList):
            self.text2.delete(1.0, END)
            for user in usersList:
                self.text2.insert(END, user + '\n')        
           
        def send(self):
            
            print "e" + self.entry_1.get()[:2] + "e"
            if self.entry_1.get()[:2] == 'th':
                self.update('Thread actif: ' + str(threading.active_count()))
                for th in threading.enumerate():
                    self.update(str(th))
            elif self.entry_1.get()[:12] == 'add poiuser ':
                print 'add ' + self.entry_1.get()[12:]
                s = self.entry_1.get()[12:]
                s1 = s.split(' ')
                for s2 in s1:
                    print s2
            else:
                self.sendAllData(self.entry_1.get())        
            
        def sendAllData(self, value):
            s = self.parent.sendData(self.sock, value)
            s.start()
            s.join()
            
        def send_FIN(self):
            self.button1.configure(text="Connect", command=self.connect)
            self.button2.configure(state='disable')
            sock.send('exit\n')
            self.th_R.exite()
            self.sock.close()
            self.th_R.join()
        def readWL(self, x):
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
        def startHTTPS(self):
            self.th_Http = self.parent.httpServer(self)        
            self.th_Http.start()
           
        def shutdHTTPS(self):
            self.th_Http.join()
            
        def connect(self):        
                    
            self.button1.configure(text='Disconnect', command=self.send_FIN)
            self.button2.configure(state='normal')
            self.update('Connecting to %s port %s' % sAddress)        
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
            sAdress = self.entry_1.get(), self.entry2.get()
            self.sock.connect(sAddress)
            self.update(u'Connexion établie avec le serveur.')
            self.th_R = self.parent.ThreadReception(self.sock, self)
            self.th_R.start()      
            self.rootM.after(6000, self.sendAllData('lp'))        
          
    class sendData(threading.Thread):
        def __init__(self, sock, value):
            threading.Thread.__init__(self)
            self.sock = sock
            self.value = value 
        def run(self):
            self.sock.send(self.value + '\n')    
   
    def run(self):
        pass
    
    class mapR(threading.Thread):
        def __init__(self, parent, value):
            threading.Thread.__init__(self)
            self.parent = parent
            self.value = value 
        def run(self):
            self.parent.parent.copyMapFile(self.parent.parent.game_player_path, self.value+".map")
            self.parent.parent.map_files = self.parent.parent.read_folder("Map")
            self.parent.parent.create_tiles(self.parent.parent.map_files, self.parent.parent.tile_path, self.parent.parent.tile_zoom, self.parent.parent.store_history)
                                       
   
    
"""thread_1 = KFP_AddPOI(None)
thread_1.start()"""
 
"""f __name__ == "__main__":
    main()"""


