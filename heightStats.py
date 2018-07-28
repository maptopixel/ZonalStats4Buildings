# -*- coding: utf-8 -*-
"""

@author: Julian Rosser
@date: Feb 2018

"""

def main(args):
    print "printing args..."
    print(args)


    footprints = args.footprints
    footprintsEdges = args.footprintsEdges
    footprintsRidgeLines = args.footprintsRidgeLines
    dsmSlopeImg = args.dsmSlopeImg
    dsmImg = args.dsmImg
    dtmImg = args.dtmImg
   
    USE_RIDGELINES = False
    USE_DTM = False
    USE_DSM = False
    USE_SLOPE = True 
         
    
    # Import GDAL, NumPy, and matplotlib
    import numpy as np
    import matplotlib.pyplot as plt
    
    
    from rasterstats import zonal_stats
    import geopandas as gpd
    import pandas as pd
    from geopandas import GeoSeries, GeoDataFrame
    
    import rasterio
        
    import logging
    logging.basicConfig(level=logging.DEBUG) # for Fiona
    

    
    print 'Setting files and vars...'


    footprintsGDF = gpd.GeoDataFrame.from_file(footprints)
    footprintsGDF.plot()
    footprintsGDF.rename(index=str, columns={"fid": "fid_1"})
    footprintsGDF = footprintsGDF.rename(columns={"fid": "fid_1"})
    footprintsGDF.columns
    
    if footprintsRidgeLines != '':
        print 'Reading ridgelines...'
        footprintMedialAxisLinesGDF = gpd.GeoDataFrame.from_file(footprintMedialAxisLines)
        footprintMedialAxisLinesGDF.plot()
    
    if footprintsRidgeLines != '':        
        #edgesGDF = gpd.GeoDataFrame.from_file(footprintsEdges)
        edgesGDF  = footprintsGDF # dont use inward buffered polys
        
    
    metrics = "min max mean median std range percentile_90".split()
    metricsSelector = list(metrics) #create new copy of list!
    metricsSelector.insert(0, "fid_1")
        
    
    # DSM data
    if USE_DSM == True:
        print 'Reading DSM...'
        # DSM data
        with rasterio.open(dsmImg) as src:
            transform = src.meta['transform']
            dsmArray = src.read_band(1)
        
        print (transform)
        dsmArray
        dsmArray[dsmArray==-9999]=np.nan
        
        allDSMShapeStats = zonal_stats(edgesGDF, dsmArray, transform=transform, nodata =-9999,geojson_out=True,stats=metrics)
        
        allDSMShapeStatsDF = GeoDataFrame.from_features(allDSMShapeStats )
        #allDSMShapeStatsDF = pd.DataFrame(allDSMShapeStats)
        allDSMShapeStatsDF=allDSMShapeStatsDF[metricsSelector]
        allDSMShapeStatsDF = allDSMShapeStatsDF.add_prefix('DSM_')
        allDSMShapeStatsDF.columns
        
    
    # DTM data
    if USE_DTM == True:
        print 'Reading DTM...'
        with rasterio.open(dtmImg) as src:
            transform = src.meta['transform']
            dtmArray = src.read_band(1)
            
            
        dtmArray
        dtmArray[dtmArray==-9999]=np.nan
        
        allDTMShapeStats = zonal_stats(edgesGDF , dtmArray,transform=transform, nodata =-9999,geojson_out=True,stats=metrics)
        allDTMShapeStatsDF = GeoDataFrame.from_features(allDTMShapeStats )
        allDTMShapeStatsDF=allDTMShapeStatsDF[metricsSelector]
        allDTMShapeStatsDF = allDTMShapeStatsDF.add_prefix('DTM_')
        allDTMShapeStatsDF.columns
    
    
    # SLOPE data
    if USE_SLOPE == True:
        print 'Reading slope...'
        import rasterio
        # SLOPE data
        with rasterio.open(dsmSlopeImg) as src:
            transform = src.meta['transform']
            slopeArray = src.read_band(1)
        
        print (transform)
        slopeArray
        slopeArray[slopeArray==-9999]=np.nan
        
        allSlopeShapeStats = zonal_stats(footprintsGDF, slopeArray, transform=transform, nodata =-9999,geojson_out=True,stats=metrics)
        
        allSlopeShapeStatsDF = GeoDataFrame.from_features(allSlopeShapeStats )
        allSlopeShapeStatsDF=allSlopeShapeStatsDF[metricsSelector]
        allSlopeShapeStatsDF = allSlopeShapeStatsDF.add_prefix('SLOP_')
        allSlopeShapeStatsDF.columns
    
           
    # CENTRE LINES
    if USE_RIDGELINES == True:
        geodfCentres = gpd.GeoDataFrame.from_file(footprintMedialAxisLines)
        geodfCentres.plot()
        ridgelineDSMShapeStats = zonal_stats(geodfCentres, dsmImg, transform=transform,geojson_out=True,all_touched=True,stats=metrics)
        ridgelineDSMShapeStatsDF =  GeoDataFrame.from_features(ridgelineDSMShapeStats )
        ridgelineDSMShapeStatsDF=ridgelineDSMShapeStatsDF[metricsSelector]
        ridgelineDSMShapeStatsDF = ridgelineDSMShapeStatsDF.add_prefix('RIDG_')
        ridgelineDSMShapeStatsDF.columns
    
    
    
    # join dsm and dtm
    footprintsGDFWithVals = footprintsGDF
    if USE_DSM == True:
        footprintsGDFWithVals = footprintsGDFWithVals.merge(allDTMShapeStatsDF, left_on='DSM_fid_1', right_on='DTM_fid_1', how='inner')
    if USE_SLOPE == True:
        footprintsGDFWithVals = footprintsGDFWithVals.merge(allSlopeShapeStatsDF, left_on='fid_1', right_on='SLOP_fid_1', how='inner')
        
    new_geodfWithDEM= footprintsGDFWithVals
    new_geodfWithDEM
    
    # Joing geopandas with ridge
    if USE_RIDGELINES == True:
        new_geodfWithDEM=new_geodfWithDEM.merge(ridgelineDSMShapeStatsDF , left_on='fid_1', right_on='RIDG_fid_1', how='outer')
        
    
    
    # plot it
    new_geodf = new_geodfWithDEM
    new_geodf.plot()
    
    
    #now create the field names according bha names
    new_geodfRev = new_geodf
    if USE_DSM == True & USE_DTM == True:
        new_geodfRev['abshmin'] = new_geodfRev['DTM_mean']
        new_geodfRev['abshmax'] = new_geodfRev['DSM_percentile_90']
        new_geodfRev['absh2'] = new_geodfRev['DSM_mean']
        new_geodfRev['relh2'] = new_geodfRev['DSM_mean'] - new_geodfRev['DTM_mean']
        new_geodfRev['relhmax'] =  new_geodfRev['DSM_percentile_90'] - new_geodfRev['DTM_mean']
        
    
    new_geodf= new_geodfRev

    
    ## Hack for defining the CRS in geopandas
    new_geodf.__class__ = gpd.GeoDataFrame
    new_geodf.crs = footprintsGDF.crs
    new_geodf.set_geometry('geometry')
    ## /hack
    
    
    print 'Writing to file...' 
    #new_geodf.to_file('output.gpkg', driver="GPKG") # Gpkg seems broken
    new_geodf.to_file('output.shp', driver="ESRI Shapefile")
                

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--footprints', default='', type=str,
        help='A building footprints polygon file, no multi-polygons and there is a unique ID per poly')
    parser.add_argument('--footprintsEdges', default='', type=str,
        help='A file of polygons corresponding to the building edges e.g result of an inward buffer')
    parser.add_argument('--footprintsRidgeLines', default='', type=str,
        help='A file of lines corresponding to the roof ridgeline e.g result of medial axis transformation')          
    parser.add_argument('--dsmImg', default='', type=str,
        help='A raster DSM')         
    parser.add_argument('--dtmImg', default='', type=str,
        help='A raster DTM')      
    parser.add_argument('--dsmSlopeImg', default='', type=str,
        help='A raster of the slope values')    
    
    args = parser.parse_args()
    
    print 'Start roof stats summary...'
    main(args)
    

