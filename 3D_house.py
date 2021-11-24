from geopy.geocoders import Nominatim
from osgeo import gdal, osr, ogr
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from urllib.request import urlopen
from zipfile import ZipFile
from io import BytesIO
import os


def plot3DMap(dataset):
    x = np.arange(0, dataset.shape[0])
    y = np.arange(0, dataset.shape[1])
    xv, yv = np.meshgrid(x, y)
    z = dataset[xv, yv]

    fig = go.Figure(
        data=[
            go.Surface(
                z=z,
                x=xv,
                y=yv,
                colorscale="Blues",
                lighting=dict(ambient=0.5, diffuse=0.5),
            )
        ]
    )
    fig.show()


def convert_coordinates(x, y):

    # Spatial Reference System
    inputEPSG = 4326
    outputEPSG = 31370

    # create coordinate transformation
    inSpatialRef = osr.SpatialReference()
    inSpatialRef.ImportFromEPSG(inputEPSG)

    outSpatialRef = osr.SpatialReference()
    outSpatialRef.ImportFromEPSG(outputEPSG)

    coordTransform = osr.CoordinateTransformation(inSpatialRef, outSpatialRef)

    # create a geometry from coordinates
    point = ogr.Geometry(ogr.wkbPoint)
    point.AddPoint(float(x), float(y))

    # transform point
    point.Transform(coordTransform)

    return point.GetX(), point.GetY()


def find_and_get_raster(x_coordinate, y_coordinate):
    ds = pd.read_csv("raster_file_list.csv")
    file_info = ds[
        ((x_coordinate >= ds["xmin"]) & (x_coordinate <= ds["xmax"]))
        & ((y_coordinate >= ds["ymin"]) & (y_coordinate <= ds["ymax"]))
    ]
    dsm_file_path = get_raster(
        "https://downloadagiv.blob.core.windows.net/dhm-vlaanderen-ii-dsm-raster-1m/DHMVIIDSMRAS1m_k",
        int(file_info.iloc[-1].file_number),
        "DSM",
    )
    dtm_file_path = get_raster(
        "https://downloadagiv.blob.core.windows.net/dhm-vlaanderen-ii-dtm-raster-1m/DHMVIIDTMRAS1m_k",
        int(file_info.iloc[-1].file_number),
        "DTM",
    )

    return dsm_file_path, dtm_file_path


def get_raster(link, file_number, file_type):
    if file_number < 10:
        file_number = "0" + str(file_number)
    file_link = link + str(file_number) + ".zip"

    file_path = os.path.abspath("geo-files/" + file_type)
    for filename in os.listdir(file_path + "/GeoTIFF"):
        if os.path.splitext(filename)[0][-2:] == str(file_number):
            return file_path + "/GeoTIFF/" + filename
    http_response = urlopen(file_link)
    zipfile = ZipFile(BytesIO(http_response.read()))
    return zipfile.extract(zipfile.namelist()[3], path=file_path)


geolocator = Nominatim(user_agent="3dhouse")
address = input("Please enter address")
location = geolocator.geocode(address).raw

del geolocator
xmin, ymin = convert_coordinates(location["boundingbox"][0], location["boundingbox"][2])
xmax, ymax = convert_coordinates(location["boundingbox"][1], location["boundingbox"][3])

latitude = location["lat"]
longitude = location["lon"]
x_coordinate, y_coordinate = convert_coordinates(latitude, longitude)

dsm_file_path, dtm_file_path = find_and_get_raster(x_coordinate, y_coordinate)

dsm_big = gdal.Open(dsm_file_path)
dtm_big = gdal.Open(dtm_file_path)

gdal.Warp(
    "geo-files/temp_files/DSM.tif",
    dsm_big,
    outputBounds=(xmin - 10, ymin - 10, xmax + 10, ymax + 10),
    dstNodata=-9999,
)
gdal.Warp(
    "geo-files/temp_files/DTM.tif",
    dtm_big,
    outputBounds=(xmin - 10, ymin - 10, xmax + 10, ymax + 10),
    dstNodata=-9999,
)

dsm = gdal.Open("geo-files/temp_files/DSM.tif")
dtm = gdal.Open("geo-files/temp_files/DTM.tif")

dsm_band = dsm.GetRasterBand(1)
dtm_band = dtm.GetRasterBand(1)
dsm_array = dsm_band.ReadAsArray()
dtm_array = dtm_band.ReadAsArray()

chm = dsm_array - dtm_array

plt.figure()
plt.imshow(chm)
plt.show()

plot3DMap(chm)
