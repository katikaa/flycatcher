from osgeo import gdal,ogr
from osgeo.gdalconst import *
import struct
import sys
import numpy as np
from geopy.distance import vincenty, Point
import argparse
import math
import requests
import bs4


# need to add your flickr, google maps API key
flickr_api_key=''
gmaps_api_key=''
# download the gpw-v4-population-count tif file in the directory (too large for github)
tif='data/gpw-v4-population-count-2015/gpw-v4-population-count_2015.tif'


gdal.UseExceptions()
ds = gdal.Open(tif)
transf = ds.GetGeoTransform()
band = ds.GetRasterBand(1)
success, transfInv = gdal.InvGeoTransform(transf)




def pt2fmt(pt):
    fmttypes = {
        GDT_Byte: 'B',
        GDT_Int16: 'h',
        GDT_UInt16: 'H',
        GDT_Int32: 'i',
        GDT_UInt32: 'I',
        GDT_Float32: 'f',
        GDT_Float64: 'f'
        }
    return fmttypes.get(pt, 'x')

def pixel2val(px, py):
    global band
    structval = band.ReadRaster(int(px), int(py), 1,1, buf_type = band.DataType )
    fmt = pt2fmt(band.DataType)
    intval = struct.unpack(fmt , structval)
    return intval[0]

def pointInEllipse(x,y,xp,yp,d,D,angle=0):
    cosa=math.cos(angle)
    sina=math.sin(angle)
    dd=d/2*d/2
    DD=D/2*D/2
    a =math.pow(cosa*(xp-x)+sina*(yp-y),2)
    b =math.pow(sina*(xp-x)-cosa*(yp-y),2)
    ellipse=(a/dd)+(b/DD)
    if ellipse <= 1:
        return True
    else:
        return False



def find_most_pop_area_within_dist(lat, lon, d=100):
    # returns lat,lon of the most populated area 
    # from point (lat,lon) within distance d km
    global ds, transf, transfInv

    origin = Point(lat, lon)
    latd={}
    lond={}
    i=0
    pxl=float('inf') 
    pxh=float('-inf')
    pyl=float('inf')
    pyh=float('-inf')
    bs = [0,90,180,270]
    for b in bs:
        destination = vincenty(kilometers=d).destination(origin, b)
        latd[i], lond[i] = destination.latitude, destination.longitude
        px, py = gdal.ApplyGeoTransform(transfInv, lond[i], latd[i])
        # print((latd[i],lond[i]))
        pxl = min(pxl,px)
        pxh = max(pxh,px)
        pyl = min(pyl,py)
        pyh = max(pyh,py)
        i+=1

    pxl = int(np.floor(pxl))
    pxh = int(np.ceil(pxh))
    pyl = int(np.floor(pyl))
    pyh = int(np.ceil(pyh))
    ed=max(latd.values())-min(latd.values())
    eD=max(lond.values())-min(lond.values())

    pxmax=0
    pymax=0
    pvmax=float('-inf')
    for px in range(pxl,pxh+1):
        for py in range(pyl,pyh+1):
            lonc, latc = gdal.ApplyGeoTransform(transf, px, py)
            if not pointInEllipse(lat,lon,latc,lonc,ed,eD): continue
            pv = pixel2val(px, py)
            if pv > pvmax:
                pvmax = pv
                pxmax = px
                pymax = py

    lonmax, latmax = gdal.ApplyGeoTransform(transf, pxmax, pymax)
    return latmax,lonmax, latd,lond


def get_city_name(lat,lon):
    # returns the name of the state/city based on the lat,lon
    # using the Google Geocode API
    url = 'https://maps.googleapis.com/maps/api/geocode/json'
    params = {'region': 'GB', 'latlng': str(lat)+','+str(lon)}
    r = requests.get(url, params=params)
    results = r.json()['results']
    location_a=''
    location_b=''
    for l in range(1,6):
        lvl='administrative_area_level_'+str(l)
        for r in range(len(results)):
            for a in results[r]['address_components']:
                if location_a == '' and lvl in a['types']:
                    location_a = a['long_name']
                if location_b == '' and 'locality' in a['types']:
                    location_b = a['long_name']
    jn=''
    if location_a!='' and location_b!='':
        jn=', '
    return location_b+jn+location_a

def get_flickr_pics(lat,lon,num=10):
    global flickr_api_key
    url = 'https://api.flickr.com/services/rest/?'
    params = {'method': 'flickr.photos.search', 'lat': str(lat), 'lon':str(lon), 'accuracy':11,
        'api_key':flickr_api_key, 'format':'json', 'nojsoncallback':1}
    r = requests.get(url, params=params)
    results = r.json()['photos']['photo']
    pics=[]
    for pi in range(min(num,len(results))):
        pic=results[pi]
        pics.append('https://farm'+str(pic['farm'])+'.staticflickr.com/'+str(pic['server'])+'/'+str(pic['id'])+'_'+str(pic['secret'])+'.jpg')
    return pics

def get_wikipages(place):
    splace=place.split(',')[0].replace(' ','_')
    wikis=['wikipedia','wikitravel']
    pages=[]
    for wiki in wikis:
        url='http://'+wiki+'.org/en/Index.php?search='+splace
        r=requests.get(url)
        if r.url != url:
            pages.append(r.url)
        else:
            soup = bs4.BeautifulSoup(r.text, "lxml")
            for headline in soup('div', {'class' : 'mw-search-result-heading'}):
                pages.append('http://wikitravel.org'+headline.a.attrs['href'])
                break
    return pages

def generate_page(city_name,lat,lon,latmax,lonmax,latd,lond,pages,pics,addmap):
    global gmaps_api_key
    template = 'outputs/prototype-gen.html'
    iframew='50'
    if addmap:
        template = 'outputs/prototype-gen-map.html'
        iframew='43'
    with open(template, 'r') as content_file:
        html = content_file.read()
    html=html.replace('@place@',city_name)
    html=html.replace('@lat@',str(lat))
    html=html.replace('@lon@',str(lon))
    html=html.replace('@latmax@',str(latmax))
    html=html.replace('@lonmax@',str(lonmax))
    html=html.replace('@lat0@',str(latd[0]))
    html=html.replace('@lon0@',str(lond[0]))
    html=html.replace('@lat90@',str(latd[1]))
    html=html.replace('@lon90@',str(lond[1]))
    html=html.replace('@lat180@',str(latd[2]))
    html=html.replace('@lon180@',str(lond[2]))
    html=html.replace('@lat270@',str(latd[3]))
    html=html.replace('@lon270@',str(lond[3]))
    if len(pages)>0:
        if len(pages)==1:
            html=html.replace('@wiki@','<iframe src="'+pages[0]+'" style="position:relative; width: 100%; height: 100%;"></iframe>');
        else:
            html=html.replace('@wiki@','<iframe src="'+pages[0]+'" style="position:relative; width: 100%; height: '+iframew+'%;"></iframe><iframe src="'+pages[1]+'" style="position:relative; width: 100%; height: '+iframew+'%;"></iframe>');
    else:
        html=html.replace('@wiki@','')
    picshtml=''
    for i in range(len(pics)):
        picshtml+='<img src="'+pics[i]+'" style="position:relative; width: 100%" />'
    html=html.replace('@pics@',picshtml)
    html=html.replace('@apikey@',gmaps_api_key)
    with open('outputs/webpage_'+str(lat)+','+str(lon)+'_'+str(latmax)+','+str(lonmax)+'.html', 'w') as wf:
         wf.write(html)


def main(): 
    parser = argparse.ArgumentParser()
    parser.add_argument("-coords", dest="coords",  help="latitude,longitude", default="51.126989,0.671135")
    parser.add_argument("--addmap", dest="addmap",  help="adds a google map to the result page", action='store_true')
    options = parser.parse_args()

    coords = options.coords
    addmap = int(options.addmap)
    coordsAr = coords.split(',');
    lat = float(coordsAr[0])
    lon = float(coordsAr[1])

    latmax,lonmax, latd, lond = find_most_pop_area_within_dist(lat,lon)
    city_coords = str(latmax)+","+str(lonmax)
    city_name = get_city_name(latmax,lonmax)
    pages=get_wikipages(city_name)
    pics=get_flickr_pics(latmax,lonmax)
    print(city_coords)
    print(city_name)
    print(pages)
    print(pics)
    generate_page(city_name,lat,lon,latmax,lonmax,latd,lond,pages,pics,addmap)




if __name__ == '__main__':
    main()


