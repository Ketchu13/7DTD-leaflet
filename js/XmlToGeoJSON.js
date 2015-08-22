var house = L.icon({
  iconUrl: './images/marker_kfp_7dtd/keystone1.png',
  iconSize: [24, 24],
  iconAnchor: [12, 12],
  popupAnchor: [0, -10]
});
var user = L.icon({
  iconUrl: './images/marker_kfp_7dtd/user.png',
  iconSize: [16, 24],
  iconAnchor: [8, 12],
  popupAnchor: [0, -10]
});
var userOff = L.icon({
  iconUrl: './images/marker_kfp_7dtd/userOff.png',
  iconSize: [16, 24],
  iconAnchor: [8, 12],
  popupAnchor: [0, -10]
});
var POIic = L.icon({
  iconUrl: './images/marker_kfp_7dtd/POI.png',
  iconSize: [16, 24],
  iconAnchor: [8, 12],
  popupAnchor: [0, -10]
});
var hot = POIic;
var house2 = L.icon({
  iconUrl: './images/marker_kfp_7dtd/house2.png',
  iconSize: [22, 22],
  iconAnchor: [11, 11],
  popupAnchor: [0, -10]
});
var farm = L.icon({
  iconUrl: './images/marker_kfp_7dtd/farm.png',
  iconSize: [22, 22],
  iconAnchor: [11, 11],
  popupAnchor: [0, -10]
});
var bank = L.icon({
  iconUrl: './images/marker_kfp_7dtd/bank.png',
  iconSize: [22, 22],
  iconAnchor: [11, 11],
  popupAnchor: [0, -10]
});
var pyramid = L.icon({
  iconUrl: './images/marker_kfp_7dtd/pyramid.png',
  iconSize: [22, 22],
  iconAnchor: [11, 11],
  popupAnchor: [0, -10]
});
var water = L.icon({
  iconUrl: './images/marker_kfp_7dtd/water.png',
  iconSize: [22, 22],
  iconAnchor: [11, 11],
  popupAnchor: [0, -10]
});
var wood = L.icon({
  iconUrl: './images/marker_kfp_7dtd/wood.png',
  iconSize: [22, 22],
  iconAnchor: [11, 11],
  popupAnchor: [0, -10]
});
var mapple = L.icon({
  iconUrl: './images/marker_kfp_7dtd/mapple.png',
  iconSize: [22, 22],
  iconAnchor: [11, 11],
  popupAnchor: [0, -10]
});
var hp = L.icon({
  iconUrl: './images/marker_kfp_7dtd/hp.png',
  iconSize: [22, 22],
  iconAnchor: [11, 11],
  popupAnchor: [0, -10]
});
var camp = L.icon({
  iconUrl: './images/marker_kfp_7dtd/camp.png',
  iconSize: [16, 16],
  iconAnchor: [8, 8],
  popupAnchor: [0, -10]
});
var LineStyle = {
    color: "#f00",
    weight: 1,
    opacity: 0.65
};


function escapeHTML(str){
    var el = document.createElement("p");
    el.appendChild(document.createTextNode(str));
    return el.innerHTML;
}

function ShowPOILocation() {
    var data =[];
    if (window.XMLHttpRequest) {// code for IE7+, Firefox, Chrome, Opera, Safari
            xmlhttp=new XMLHttpRequest();
    } else {// code for IE6, IE5
            xmlhttp=new ActiveXObject("Microsoft.XMLHTTP");
    }
    xmlhttp.open("GET", "./xml/POIList.xml", false);
    xmlhttp.send();
    xmlDoc=xmlhttp.responseXML;
    var pois = xmlDoc.getElementsByTagName("poilist")[0].getElementsByTagName("poi");
        if(! pois.length == 0 ) {
            try {
                for (var j = 0; j < pois.length; j++) {
                    var Id = pois[j].getAttribute("id");
                    var steamId = pois[j].getAttribute("steamId");
                    var lpblock = pois[j].getAttribute("pos").split(",");
                    var pname =  pois[j].getAttribute("pname");
                    var sname =  pois[j].getAttribute("sname");
                    var icone =  pois[j].getAttribute("icon");
                    var name = pois[j].getAttribute("name");
                        var ct = escapeHTML(pname) + "<br>Signaled by " + escapeHTML(sname);
                        var prop0 = {
                            "icon": window[icone],
                            "popupContent": ct,
                            "entity": 1,
                            "hidden": false
                        };
                        var data3 = {
                            "type": "Feature",
                            "geometry": {
                                "type": "Point",
                                "coordinates": [lpblock[1], lpblock[0]]
                            },
                            "properties": prop0
                        };

                        data.push(data3);
                }
            } catch(ex){alert(ex);}
        }
    return [{"type": "FeatureCollection", "features": data }];
}