#!/usr/bin/env python
# -*- coding: utf-8 -*-
import SocketServer
import BaseHTTPServer
import sys, os
import cgitb; cgitb.enable()
import CGIHTTPServer
port = 8081


class ThreadingCGIServer(SocketServer.ThreadingMixIn, BaseHTTPServer.HTTPServer):
    pass
server = ThreadingCGIServer(('', port), CGIHTTPServer.CGIHTTPRequestHandler)
print "Serveur demarre sur le port %s." % port
try:
    while 1:
        sys.stdout.flush()
        server.handle_request()
except KeyboardInterrupt:
    print "Fini !"
