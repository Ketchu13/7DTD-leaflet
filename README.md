7DTD-leaflet
============

Merge 7DTD discovered map in html for www.ketchu-free-party.fr

The python script map_reader.py will extract dans merge all .map files of a random world.
The result is then saved into png files.

A javascript code (Leaflet) merge all this png files while browsing the big map.

How to use
=============

Install:

 * Python 2.7 https://www.python.org/downloads/
 * Pillow https://pillow.readthedocs.org/en/latest/
 
Run map_reader.py a gui will ask you the path of the .map folder.

A sub directory named tiles will be created.

Open index.html in your brower.

You can also use it in command line.

```bash
python map_reader.py -s 127.0.0.1:8081 -p CHANGEME -c "." -g "C:\Users\...\AppData\Roaming\7DaysToDie\Saves\Random Gen\...\Player" -k "./xml/POIList.xml" -h 8082 -w "./xml/POIWhiteList.xml" -v True -b gui -f ftpHost:username:password
```
or simply edit Config.kfp values.

Usage:
===============
```bash
map_reader -g XX [options]
 -g "C:\Users..":        The folder that contain .map files
 -t "tiles":             The folder that will contain tiles (Optional)
 -z 8:                           Zoom level 4-n. Number of tiles to extract arou
nd position 0,0 of map.
 It is in the form of 4^n tiles.It will extract a grid of 2^n*16 tiles on each s
ide.(Optional)
 -s telnethost:port     7DTD server ip and port (telnet port, default 8081) (Opt
ional)
 -p CHANGEME Password of telnet, default is CHANGEME (Optional)
 -i True         Do not read /addpoi command of players
 -x True         Do not write players track in csv files
 -h 8080 Http Server Port(default 8081) (Optional)
 -w "C:\...\xml\whitelist.xml":          Authorized users list path...
 -k "C:\...\xml\POIList.xml":            POI list xml...
 -v True                                 Show received data (0=False, 1=True)...

 -c "www":               The folder that contain your index.html (Optional)
 -newest Keep track of updates and write the last version of tiles. This will sh
ow players bases on map.(Optional)
 -b gui:                 Use Gui version (Optional)
 -f FTPHost:Port:UserName:PassWord       FTP server connection infos (Optional)
```

Additonnal content
==============

You can also show where your players gone by editing an updating the "players/tracks.csv" file.

Lat long is the ingame coordinates.

GUI Version
==============

![alt tag](https://raw.github.com/Ketchu13/7DTD-leaflet/master/images/screenshots/02.10.08.png)


The content of the file is only showed if you publish the website through a web server.
You can run simple_server.py to give access on http://localhost:8000 .

Remember that python files are under GPLv3 license and then you need to redistribute your modifications.
