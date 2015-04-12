var farm = L.icon({
  iconUrl: './images/marker/farm.png',
  iconSize: [22, 22],
  iconAnchor: [11, 11],
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
	xmlhttp.open("GET", "POIList.xml", false);
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
								"coordinates": [lpblock[0], lpblock[2]]
							},						
							"properties": prop0
						};							
						 
						data.push(data3);
				}
			} catch(ex){alert(ex);}
		} 
	return [{"type": "FeatureCollection", "features": data }];
}