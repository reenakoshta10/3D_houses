from geopy.geocoders import Nominatim
from osgeo import gdal, osr
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Point, LineString, Polygon
from mpl_toolkits import mplot3d
from bs4 import BeautifulSoup
import requests 
import shapefile
# import warnings
# warnings.filterwarnings('ignore')
address = "Kasteelplein 1, 2300 Turnhout"

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
                gdal.Warp("geo-files/temp_files/"+filename+".tif", dem, 
                          outputBounds = (xmin, ymin, xmax, ymax), dstNodata = -9999)

def get_coordinates(address: str):
    req = requests.get(f"https://loc.geopunt.be/v4/Location?q="+address).json()
    # print(req)
    info = {'address' : address, 
                'x_value' : req['LocationResult'][0]['Location']['X_Lambert72'],
                'y_value' : req['LocationResult'][0]['Location']['Y_Lambert72'],
                'street' : req['LocationResult'][0]['Thoroughfarename'],
                'house_number' : req['LocationResult'][0]['Housenumber'], 
                'postcode': req['LocationResult'][0]['Zipcode'], 
                'municipality' : req['LocationResult'][0]['Municipality']}
#     info ={}
    detail = requests.get("https://api.basisregisters.vlaanderen.be/v1/adresmatch", 
                          params={"postcode": info['postcode'], 
                                  "straatnaam": info['street'],
                                  "huisnummer": info['house_number']}).json()
    building = requests.get(detail['adresMatches'][0]['adresseerbareObjecten'][0]['detail']).json()
    build = requests.get(building['gebouw']['detail']).json()
    info['polygon'] = [build['geometriePolygoon']['polygon']]
    points = info['polygon'][0]['coordinates'][0] 
    return info

coordinates = get_coordinates(address)
x_coordinate = coordinates['x_value']
y_coordinate = coordinates['y_value']

dsm_big = gdal.Open("geo-files/DHMVIIDSMRAS1m_k08/GeoTIFF/DHMVIIDSMRAS1m_k08.tif")
dtm_big = gdal.Open("geo-files/DHMVIIDTMRAS1m_k08/GeoTIFF/DHMVIIDTMRAS1m_k08.tif")

createSmallRaster(dsm_big, x_coordinate, y_coordinate, "DSM")
createSmallRaster(dtm_big, x_coordinate, y_coordinate, "DTM")

dsm= gdal.Open("geo-files/temp_files/DSM.tif")
dtm= gdal.Open("geo-files/temp_files/DTM.tif")

dsm_array = dsm.ReadAsArray()
dtm_array = dtm.ReadAsArray()

chm = dsm_array - dtm_array

plt.figure(figsize=(20,10))
plt.imshow(chm)

ny, nx = chm.shape
x = np.arange(0,chm.shape[0])
y = np.arange(0,chm.shape[1])
xv, yv = np.meshgrid(x, y)
z = chm[xv,yv]

fig = plt.figure(figsize=(20,10))
ax = fig.add_subplot(111, projection='3d')
plt.xticks(rotation=90)
dem3d=ax.plot_surface(xv,yv,z)
plt.show()

# w = shapefile.Writer('geo-files/shapefiles/polygon')
# w.field('name', 'C')

# w.poly([
#         coordinates['polygon'][0]['coordinates'][0]   # poly 2
#         ])
# w.record('polygon1')

# w.close()

from osgeo import ogr
from shapely.geometry import Polygon

# Here's an example Shapely geometry
poly = Polygon(coordinates['polygon'][0]['coordinates'][0])

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

gdal.UseExceptions()

infile = "geo-files/DHMVIIDSMRAS1m_k08/GeoTIFF/DHMVIIDSMRAS1m_k08.tif"
shapefile = 'geo-files/shapefiles/polygon.shp'
outfile = 'geo-files/shapefiles/polygon.tif'

result = gdal.Warp(outfile, infile, cutlineDSName = shapefile)

final_file = gdal.Open(outfile)
createSmallRaster(final_file, x_coordinate, y_coordinate, "out")

last_file = gdal.Open("geo-files/temp_files/out.tif")

outarr= last_file.ReadAsArray()
chm = outarr - dtm_array
plt.figure(figsize=(20,10))
plt.imshow(chm)

ny, nx = chm.shape
x = np.arange(0,chm.shape[0])
y = np.arange(0,chm.shape[1])
xv, yv = np.meshgrid(x, y)
z = chm[xv,yv]

fig = plt.figure(figsize=(20,10))
ax = fig.add_subplot(111, projection='3d')
plt.xticks(rotation=90)
dem3d=ax.plot_surface(xv,yv,z)
plt.show()