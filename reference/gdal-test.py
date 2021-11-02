from osgeo import gdal
import numpy as np
import matplotlib.pyplot as plt

ds = gdal.Open("geo-files/DHMVIIDSMRAS1m_k01/GeoTIFF/DHMVIIDSMRAS1m_k01.tif")
gt = ds.GetGeoTransform()
proj = ds.GetProjection()

band = ds.GetRasterBand(1)
array = band.ReadAsArray()

plt.figure()
plt.imshow(array)
plt.colorbar()
plt.show()

# band = ds.GetRasterBand(1)
# array = band.ReadAsArray()

# plt.figure()
# plt.imshow(array)

# manipulate
# binmask = np.where((array >= np.mean(array)),1,0)
# plt.figure()
# plt.imshow(binmask)

# export
# driver = gdal.GetDriverByName("GTiff")
# driver.Register()
# outds = driver.Create("binmask.tif", xsize = binmask.shape[1],
#                       ysize = binmask.shape[0], bands = 1, 
#                       eType = gdal.GDT_Int16)
# outds.SetGeoTransform(gt)
# outds.SetProjection(proj)
# outband = outds.GetRasterBand(1)
# outband.WriteArray(binmask)
# outband.SetNoDataValue(np.nan)
# outband.FlushCache()

# # close your datasets and bands!!!
# outband = None
# outds = None