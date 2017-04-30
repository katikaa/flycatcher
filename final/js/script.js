// script.js

var tiles = [
  'http://tile.stamen.com/toner/{z}/{x}/{y}.png',
  'http://{s}.tiles.mapbox.com/v3/osmbuildings.lgh43kca/{z}/{x}/{y}.png',
  'http://{s}.tiles.mapbox.com/v3/osmbuildings.kbpalbpk/{z}/{x}/{y}.png'];

var data = {
  athens: { lon: 23.7275, lat: 37.9838 },
  london : { lon: 51.5074, lat: 0.1278 },
  current : { lon: 51.5074, lat: 0.1278 },
  prev : { lon: 51.5074, lat: 0.1278 },
  zoom : 8.5, /*15.5*/
  tilt : 30.0,
  d: 0.002,
  tile: tiles[2],
  labels: [],
  osmb: null,
  pointer : null,
  initialized: false,
  init: function(lat, lon) {
    var w = window,
      d = document,
      e = d.documentElement,
      g = d.getElementsByTagName('body')[0],
      x = w.innerWidth || e.clientWidth || g.clientWidth,
      y = w.innerHeight|| e.clientHeight|| g.clientHeight;
    var info = document.getElementById('info');
    info.style.left = Math.round(x * 0.6) + 'px';
    info.style.top = 0 + 'px';
    info.style.width = Math.round(x * 0.4) + 'px';

    if ( null == lat || typeof lat == 'undefined'){ lat = this.current.lat; }
    if ( null == lon || typeof lon == 'undefined'){ lon = this.current.lon; }
    this.current.lat = lat;
    this.current.lon = lon;

    this.osmb = new OSMBuildings({
      position: {
        latitude: lat,
        longitude: lon
      },
      zoom: this.zoom,
      tilt: this.tilt,
      // minZoom: 6,
      // maxZoom: 10,
      state: true,
      fastMode: true,
      elevation: 0.8,
    });
    this.osmb.appendTo('map');
    this.osmb.addMapTiles(this.tile,{attribution: '-'});
    this.osmb.addGeoJSONTiles(
      'http://{s}.data.osmbuildings.org/0.2/anonymous/tile/{z}/{x}/{y}.json');
    this.pointer = this.osmb.addGeoJSON({
      type: 'FeatureCollection',
        features: [{ 
          type: 'Feature',
          properties:{color:'#00cc00',roofColor:'#22dd00',height:10,minHeight:10},
          geometry:{
            type:'Polygon',
            coordinates:[[
              [lon, lat],
              [lon - this.d, lat - this.d],
              [lon + this.d, lat - this.d],
              [lon, lat],
            ]]
          }
        }]
    });
    document.addEventListener('keydown', function(e) {
      var transInc = e.altKey ? 0.002 : 0.0002;
      var scaleInc = e.altKey ? 0.1 : 0.01;
      var rotaInc = e.altKey ? 10 : 1;
      var eleInc = e.altKey ? 10 : 1;
      switch (e.which) { 
        case 37:
          data.current.lon -= transInc;
          data.move(data.current.lat, data.current.lon);
          break;
        case 39:
          data.current.lon += transInc;
          data.move(data.current.lat, data.current.lon);
          break;
        case 38:
          data.current.lat += transInc;
          data.move(data.current.lat, data.current.lon);
          break;
        case 40: 
          data.current.lat -= transInc;
          data.move(data.current.lat, data.current.lon);
          break;
        default: return;
      }
    });
    // this.osmb.on('change', function() { this.update_labels(); });
    this.initialized = true;
  },
  move : function(lat, lon){
    data.current.lat = lat;
    data.current.lon = lon;
    this.osmb.setPosition({latitude: lat,longitude: lon});
    this.pointer.position.latitude = lat;
    this.pointer.position.longitude = lon;
    this.update_labels();
  },
  addlabel : function(lat, lon, text, options){
    var pos          = this.osmb.project(lat, lon, 50);
    var div          = document.createElement('div');
    div.className    = 'label';
    div.style.left   = Math.round(pos.x) + 'px';
    div.style.top    = Math.round(pos.y) + 'px';
    if (options != null && typeof options != 'undefined'){
      if ( options.width != null && typeof options.width != 'undefined' ){
        div.style.width  = options.width + 'px';
      }
      if ( options.height != null && typeof options.height != 'undefined' ){
        div.style.height  = options.height + 'px';
      }
    }
    div.innerHTML    = text;
    document.getElementById('labels').appendChild(div);
    this.labels.push({el:div,lat:lat,lon:lon});
  },
  update_labels: function(){
    for (var i = this.labels.length-1; i >= 0; i--) {
      var pos = this.osmb.project(this.labels[i].lat, this.labels[i].lon, 50);
      this.labels[i].el.style.left = Math.round(pos.x) + 'px';
      this.labels[i].el.style.top = Math.round(pos.y) + 'px';
    };
  }
};

function initialized() {
    if(data.initialized == false) {
      window.setTimeout(initialized, 100); 
    } else {
      console.log(data.current);
    }
}

