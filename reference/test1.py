import gdal

def rasterise_me(raster, vector, attribute,
                fname_out="", format="MEM"):
    """Rasterises a vector dataset by attribute to match a given
    raster dataset. This functions allows for the raster and vector
    to have different projections, and will ensure that the output
    is consistent with the input raster.
    
    By default, it returns a handle to an open GDAL dataset that you
    can e.g. `ReadAsArray`. If you want to generate a  GTiff on disk,
    set format to `GTiff` and `fname_out` to a sensible filename.
    
    Parameters
    ----------
    raster: str
        The raster filaname used as input. It will not be overwritten.
    vector: str
        The vector filename
    attribute: str
        The attribute that you want to rasterize. Ideally, this is
        numeric.
    fname_out: str, optional
        The output filename.
    format: str, optional
        The output file format, such as GTiff, or whatever else GDAL
        understands
    """
    # Open input raster file. Need to do this to figure out
    # extent, projection & resolution.
    g = gdal.Open(raster) 
    geoT = g.GetGeoTransform()
    nx, ny = g.RasterXSize, g.RasterYSize 
    srs = g.GetProjection()
    min_x = min(geoT[0], geoT[0]+nx*geoT[1])
    max_x = max(geoT[0], geoT[0]+nx*geoT[1])
    min_y = min(geoT[3], geoT[3] + geoT[-1]*ny)
    max_y = max(geoT[3], geoT[3] + geoT[-1]*ny)
    # Reproject vector to match raster file
    vector_tmp = gdal.VectorTranslate("", vector, format="Memory",
                                    dstSRS=srs)
    # Do the magic
    ds_dst= gdal.Rasterize(fname_out, vector_tmp, attribute=attribute,
                        outputSRS=srs, xRes=geoT[1], yRes=geoT[-1],
                        outputBounds=[min_x, min_y, max_x, max_y],
                        format=format, outputType=gdal.GDT_Int32)
    return ds_dst


resp = rasterise_me("geo-files/DHMVIIDSMRAS1m_k08/GeoTIFF/DHMVIIDSMRAS1m_k08.tif", "geo-files/shapefiles/polygon.shp", "crop")

type(resp)

