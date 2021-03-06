from bs4 import BeautifulSoup
import requests
from urllib.request import urlopen
from io import BytesIO
from zipfile import ZipFile
from osgeo import gdal, osr, ogr
import os
import shutil
import time
import pandas as pd


def download_and_unzip(url, extract_to):
    http_response = urlopen(url)
    zipfile = ZipFile(BytesIO(http_response.read()))
    zipfile.extractall(path=extract_to)

file_links=[]
file_path = os.path.abspath("../geo-files/temp1/")
response= requests.get("http://www.geopunt.be/download?container=dhm-vlaanderen-ii-dsm-raster-1m&title=Digitaal%20Hoogtemodel%20Vlaanderen%20II,%20DSM,%20raster,%201m")
soup = BeautifulSoup(response.content)
download_links = soup.find('div', attrs={"class":"downloadfileblock"})
for link in download_links.find_all('a'):
    zipfile = link.get("href").split("/")[-1]
    zipfile_number = zipfile.split(".")[0][-2:]
    print(zipfile_number)
    time.sleep(5) 
        
    download_and_unzip(link.get("href"), file_path)
    geofile = '' 
    for filename in os.listdir(file_path+"/GeoTIFF"):
        if os.path.splitext(filename)[1]==".tif":
            geofile = filename
            ds = gdal.Open(os.path.abspath(file_path+"/GeoTIFF/"+ geofile))
            tran = ds.GetGeoTransform()
            res_x = tran[1]
            res_y = tran[5]
            xmin = tran[0]
            ymax = tran[3]
            xmax = tran[0] + res_x * ds.RasterXSize
            ymin = tran[3] + res_y * ds.RasterXSize
            file_coordinate_map={"file_number":zipfile_number, "xmin":xmin, "ymin": ymin,"xmax":xmax, "ymax": ymax}
            file_links.append(file_coordinate_map)
    try:
        shutil.rmtree(os.path.abspath("../geo-files/temp1/"))
    except OSError as e:
        print("Error: %s " % (e.strerror))
#     print(file_links)
df = pd.DataFrame(file_links)
df.to_csv("../raster_file_list.csv",mode = 'a', index=False)