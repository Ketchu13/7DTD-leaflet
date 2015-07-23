::Addpoi Usage: 
::    -i "127.0.0.1":			The server ip.
::    -p 8081:				The server port number.
::    -z "CHANGEME":			The server password.
::    -w "C:\...\POIwhitelist.xml":	Authorized users list path.
::    -k "C:\...\POIList.xml":		POI list xml.
::    -v 1:				Show received data (0=False, 1=True).

kfp_addpoi.py -i "127.0.0.1" -p 8081 -z CHANGEME -w "POIwhitelist.xml" -k "POIList.xml" -v 1