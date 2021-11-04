from geopy.geocoders import Nominatim
from osgeo import gdal, osr, ogr
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d
from bs4 import BeautifulSoup
import requests 
import shapefile
from shapely.geometry import Polygon
import plotly.graph_objects as go
import pandas as pd
from urllib.request import urlopen
from io import BytesIO
from zipfile import ZipFile
import os

def createSmallRaster(raster_ds, x, y, filename):
    dem = raster_ds
    gt = dem.GetGeoTransform()

    # get coordinates of upper left corner
    xmin = gt[0]
    ymax = gt[3]
    res = gt[1]

    # determine total length of raster
    xlen = res * dem.RasterXSize
    ylen = res * dem.RasterYSize

    # number of tiles in x and y direction
    xdiv = 200
    ydiv = 200

    # size of a single tile
    xsize = xlen/xdiv
    ysize = ylen/ydiv

    # create lists of x and y coordinates
    xsteps = [xmin + xsize * i for i in range(xdiv+1)]
    ysteps = [ymax - ysize * i for i in range(ydiv+1)]

    # loop over min and max x and y coordinates
    for i in range(xdiv):
        for j in range(ydiv):
            xmin = xsteps[i]
            xmax = xsteps[i+1]
            ymax = ysteps[j]
            ymin = ysteps[j+1]

            # use gdal warp
            if((x>=xmin and x<=xmax) and (y>=ymin and y<=ymax)):
                gdal.Warp("geo-files/temp/"+filename+".tif", dem, 
                          outputBounds = (xmin, ymin, xmax, ymax), dstNodata = -9999)
    
def createSmallRaster(raster_ds, shape, filename):
    dem = raster_ds
#     gt = dem.GetGeoTransform()

    x= [point[0] for point in shape]
    y= [point[1] for point in shape]
    
    # get coordinates of upper left corner
    xmin = min(x)
    ymax = max(y)
    xmax = max(x)
    ymin = min(y)

#     # determine total length of raster
#     xlen = res * dem.RasterXSize
#     ylen = res * dem.RasterYSize

#     # number of tiles in x and y direction
#     xdiv = 200
#     ydiv = 200

#     # size of a single tile
#     xsize = xlen/xdiv
#     ysize = ylen/ydiv

#     # create lists of x and y coordinates
#     xsteps = [xmin + xsize * i for i in range(xdiv+1)]
#     ysteps = [ymax - ysize * i for i in range(ydiv+1)]

#     # loop over min and max x and y coordinates
#     for i in range(xdiv):
#         for j in range(ydiv):
#             xmin = xsteps[i]
#             xmax = xsteps[i+1]
#             ymax = ysteps[j]
#             ymin = ysteps[j+1]

#             # use gdal warp
#             if((x>=xmin and x<=xmax) and (y>=ymin and y<=ymax)):
#                 gdal.Warp("geo-files/temp_files/"+filename+".tif", dem, 
#                           outputBounds = (xmin, ymin, xmax, ymax), dstNodata = -9999)
    gdal.Warp("geo-files/temp/"+filename+".tif", dem, 
                          outputBounds = (xmin-5, ymin-5, xmax+5, ymax+5), dstNodata = -9999)
                
def get_coordinates(address: str):
    req = requests.get(f"https://loc.geopunt.be/v4/Location?q="+address).json()
    info = {'address' : address, 
                'x_value' : req['LocationResult'][0]['Location']['X_Lambert72'],
                'y_value' : req['LocationResult'][0]['Location']['Y_Lambert72'],
                'street' : req['LocationResult'][0]['Thoroughfarename'],
                'house_number' : req['LocationResult'][0]['Housenumber'], 
                'postcode': req['LocationResult'][0]['Zipcode'], 
                'municipality' : req['LocationResult'][0]['Municipality']}
    detail = requests.get("https://api.basisregisters.vlaanderen.be/v1/adresmatch", 
                          params={"postcode": info['postcode'], 
                                  "straatnaam": info['street'],
                                  "huisnummer": info['house_number']}).json()
    building = requests.get(detail['adresMatches'][0]['adresseerbareObjecten'][0]['detail']).json()
    build = requests.get(building['gebouw']['detail']).json()
    info['polygon'] = [build['geometriePolygoon']['polygon']]
    points = info['polygon'][0]['coordinates'][0] 
    return info

def create_shapefile(polygon):
    poly = Polygon(polygon)

    directory = "shapefiles"
    parent_dir = os.path.abspath("geo-files")
    path = os.path.join(parent_dir, directory) 
    try:
        os.makedirs(path, exist_ok = True)
    except OSError as error:
        pass
    # Now convert it to a shapefile with OGR    
    driver = ogr.GetDriverByName('Esri Shapefile')
    ds = driver.CreateDataSource('geo-files/shapefiles/polygon.shp')

    srs = osr.SpatialReference()
    srs.ImportFromEPSG(31370)

    layer = ds.CreateLayer('crop', srs, ogr.wkbPolygon)
    # Add one attribute
    layer.CreateField(ogr.FieldDefn('id', ogr.OFTInteger))
    defn = layer.GetLayerDefn()

    ## If there are multiple geometries, put the "for" loop here

    # Create a new feature (attribute and geometry)
    feat = ogr.Feature(defn)
    feat.SetField('id', 123)

    # Make a geometry, from Shapely object
    geom = ogr.CreateGeometryFromWkb(poly.wkb)
    feat.SetGeometry(geom)

    layer.CreateFeature(feat)
    feat = geom = None  # destroy these

    # Save and close everything
    ds = layer = feat = geom = None
    
def plot3DMap(dataset):
    ny, nx = dataset.shape
    x = np.arange(0,dataset.shape[0])
    y = np.arange(0,dataset.shape[1])
    xv, yv = np.meshgrid(x, y)
    z = dataset[xv,yv]

    fig = plt.figure(figsize=(20,10))
    ax = fig.add_subplot(111, projection='3d')
    plt.xticks(rotation=90)
    dem3d=ax.plot_surface(xv,yv,z)
    plt.show()
    
    fig = go.Figure(data=[go.Surface(z=z, x=x, y=y)])
    fig.show()

def find_and_get_raster(x_coordinate, y_coordinate):
    ds = pd.read_csv("raster_file_list.csv")
    file_info = ds[((x_coordinate>=ds['xmin']) & (x_coordinate<=ds['xmax'])) & ((y_coordinate>=ds['ymin']) & (y_coordinate<=ds['ymax']))]
    print(file_info)
    dsm_file_path = get_raster("https://downloadagiv.blob.core.windows.net/dhm-vlaanderen-ii-dsm-raster-1m/DHMVIIDSMRAS1m_k",int(file_info.iloc[-1].file_number),'DSM')
    dtm_file_path = get_raster("https://downloadagiv.blob.core.windows.net/dhm-vlaanderen-ii-dtm-raster-1m/DHMVIIDTMRAS1m_k",int(file_info.iloc[-1].file_number),'DTM')
    
    print(dsm_file_path)
    print(dtm_file_path)
    return dsm_file_path, dtm_file_path
    
def get_raster(link,file_number,file_type):
    if file_number < 10:
        file_number = '0'+str(file_number)
    print(file_number)    
    file_link= link+str(file_number)+".zip"
    
    directory = "GeoTIFF"
    parent_dir = os.path.abspath("geo-files/temp/"+file_type)
    path = os.path.join(parent_dir, directory) 
    try:
        os.makedirs(path, exist_ok = True)
    except OSError as error:
        pass
    file_path = os.path.abspath("geo-files/temp/"+file_type)
    for filename in os.listdir(file_path+"/GeoTIFF"):
        print(os.path.splitext(filename)[0][-2:])
        if os.path.splitext(filename)[0][-2:]==str(file_number):
            return file_path+"/GeoTIFF/"+filename
    print(file_link)
    http_response = urlopen(file_link)
    zipfile = ZipFile(BytesIO(http_response.read()))
    zipfile.extractall(path=file_path)
    
    for filename in os.listdir(file_path+"/GeoTIFF"):
        if os.path.splitext(filename)[1]==".tif" and os.path.splitext(filename)[0][-2:]==str(file_number):
            geofile = filename
            path= os.path.abspath(file_path+"/GeoTIFF/"+ geofile)
            return path
        
    return None

# address = "Kasteelplein 1, 2300 Turnhout"
# address = "Koning Albertstraat 20, 2300 Turnhout"
# address = "Koningin Astridplein 27, 2018 Antwerpen"
address = input("Enter building address to get a 3D view: ")

coordinates = get_coordinates(address)
x_coordinate = coordinates['x_value']
y_coordinate = coordinates['y_value']

polygon = coordinates['polygon'][0]['coordinates'][0]
# print(coordinates)

create_shapefile(polygon)
dsm_file_path, dtm_file_path = find_and_get_raster(x_coordinate, y_coordinate)

gdal.UseExceptions()

# infile = "geo-files/DHMVIIDSMRAS1m_k08/GeoTIFF/DHMVIIDSMRAS1m_k08.tif"
# infile = "geo-files/temp/DSM/GeoTIFF/DHMVIIDSMRAS1m_k15.tif"
shape_file = 'geo-files/shapefiles/polygon.shp'
outfile = 'geo-files/shapefiles/dsm.tif'

gdal.Warp(outfile, dsm_file_path, cutlineDSName = shape_file)

# infile = "geo-files/DHMVIIDTMRAS1m_k08/GeoTIFF/DHMVIIDTMRAS1m_k08.tif"
# infile = "geo-files/temp/DTM/GeoTIFF/DHMVIIDTMRAS1m_k15.tif"
outfile = 'geo-files/shapefiles/dtm.tif'

gdal.Warp(outfile, dtm_file_path, cutlineDSName = shape_file)


dsm_big = gdal.Open("geo-files/shapefiles/dsm.tif")
dtm_big = gdal.Open("geo-files/shapefiles/dtm.tif")

# createSmallRaster(dsm_big, x_coordinate, y_coordinate, "DSM")
# createSmallRaster(dtm_big, x_coordinate, y_coordinate, "DTM")

createSmallRaster(dsm_big, polygon, "DSM")
createSmallRaster(dtm_big, polygon, "DTM")

dsm= gdal.Open("geo-files/temp/DSM.tif")
dtm= gdal.Open("geo-files/temp/DTM.tif")

dsm_array = dsm.ReadAsArray()
dtm_array = dtm.ReadAsArray()

chm = dsm_array - dtm_array

plt.figure(figsize=(20,10))
plt.imshow(chm)

plot3DMap(chm)

