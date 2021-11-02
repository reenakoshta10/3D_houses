from osgeo import gdal

dem = gdal.Open("geo-files/DHMVIIDSMRAS1m_k01/GeoTIFF/DHMVIIDSMRAS1m_k01.tif")
gt = dem.GetGeoTransform()

# get coordinates of upper left corner
xmin = gt[0]
ymax = gt[3]
res = gt[1]

# determine total length of raster
xlen = res * dem.RasterXSize
ylen = res * dem.RasterYSize

# number of tiles in x and y direction
xdiv = 10
ydiv = 10

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
        
#         print("xmin: "+str(xmin))
#         print("xmax: "+str(xmax))
#         print("ymin: "+str(ymin))
#         print("ymax: "+str(ymax))
#         print("\n")
        
        # use gdal warp
        gdal.Warp("geo-files/small_files/DSM"+str(i)+str(j)+".tif", dem, 
                  outputBounds = (xmin, ymin, xmax, ymax), dstNodata = -9999)
        # or gdal translate to subset the input raster
        gdal.Translate("geo-files/small_files/dsm_translate"+str(i)+str(j)+".tif", dem, projWin = (xmin, ymax, xmax, ymin), xRes = res, yRes = -res)
 
# close the open dataset!!!
dem = None