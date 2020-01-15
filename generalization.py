# -*- coding: utf-8 -*-
# importing modules
import os,sys
import arcpy 
from arcpy import env
from arcpy.sa import *
import arcpy.da 
import time

# check licenses 
arcpy.CheckOutExtension("Spatial")
arcpy.CheckOutExtension("3D")
arcpy.env.overwriteOutput = True

# input parameters
mainDir = r'D:\mandra_test'
streams = r'D:\mandra_test\HN\streams.shp'

start_time = time.time()

# Setnull the initial Raster with the water depths in order to convert it later to polygon.
def setnull(mainDir):
    # we choose not to define the data type in order to have all the data available in a single workspace. 
    walk = arcpy.da.Walk(mainDir, topdown = True)
    
    for folderPath, folderNames, fileNames in walk:
        if 'CN' in folderPath:
            workspace = env.workspace = folderPath
                    
            # define the output name and path 
            depth_outGrid_Name = os.path.basename(workspace) + '_stnull.tif'
            depth_outGrid_fullPath = os.path.join(workspace, depth_outGrid_Name)
              
            if fileNames[0].endswith('.tif'):
                Depth_Grid = arcpy.Raster(fileNames[0])
                                           
                setNull_Depth_Grid = SetNull(Depth_Grid, 1, "VALUE < 0") 
                setNull_Depth_Grid.save(depth_outGrid_fullPath)
                
                print  depth_outGrid_fullPath                   
          
#  Convert Set null Raster to polygon

def polygon_processing(mainDir):
    walk = arcpy.da.Walk(mainDir, topdown = True)

    for folderPath, folderNames, fileNames in walk:
         
        if 'CN' in folderPath:
            workspace = env.workspace = folderPath
             
            # The fileNames variable in fact is a list with the name of the rasters that exist inside each folder. Every time we create a new raster the list's length grows
            # per one. So, we create the index variable in order to be able to manipulate dynamically the newest raster. 
            
            index = len(fileNames) - 1
             
            if fileNames[index].endswith('_stnull.tif'):
                
                stNull_Grid = arcpy.Raster(fileNames[index])
                
                # Define the output name and path
                polygon_Name = os.path.basename(workspace) + 'poly.shp'
                polygon_fullPath = os.path.join(workspace, polygon_Name)
                
                # Raster to polygon conversion
                polygon_Depth = arcpy.RasterToPolygon_conversion(stNull_Grid, polygon_fullPath, "NO_SIMPLIFY", "VALUE") # convert raster to polygon
                 
                # Denote the spatial reference and calculate polygon area in squared meters.
                sp_Ref = arcpy.env.outputCoordinateSystem = arcpy.Describe(polygon_Depth).spatialReference
                polygon_geometry = arcpy.AddGeometryAttributes_management (polygon_Depth, "AREA", "METERS", "SQUARE_METERS",sp_Ref)
                             
                # Spatial Join the Water depth polygon with streams layer --> Intersect with 2m distance
                targetFeature = polygon_Depth 
                joinFeature = streams  
                # define the output spatial join name and path         
                outputName, file_extension = os.path.splitext(os.path.basename(polygon_fullPath)) # isolate only the filename without any prefix of the shape file
                outputName = outputName + '_SpJoin.shp'
                SpJoin_output_path = os.path.join(workspace,outputName)
                SpatialJoin_with_Streams = arcpy.SpatialJoin_analysis(targetFeature, joinFeature, SpJoin_output_path, 
                                                                      "JOIN_ONE_TO_ONE", "KEEP_ALL", "#","INTERSECT", "2 Meters", "")
                 
                print  SpatialJoin_with_Streams

# Perform the minimum mapping unit (mmu) in the spatial joined water depth polygons.             
def mmu(mainDir): 
    walk = arcpy.da.Walk(mainDir, topdown = True)
             
    for folderPath, folderNames, fileNames in walk:
          
        if 'CN' in folderPath:
            workspace = env.workspace = folderPath
              
            index = len(fileNames) - 1
          
            if fileNames[index].endswith('_SpJoin.shp'):
                Sp_joined_poly = fileNames[index]
                  
                print Sp_joined_poly
                  
                mmu_name = os.path.basename(workspace) + '_mmu.shp'
                mmu_fullPath = os.path.join(workspace, mmu_name)
                
                # copy the spatial joined polygon and denoted as the output polygon shape file, 
                #where deleting the mmu records will be performed. 
                mmu_copied_fc = arcpy.CopyFeatures_management(Sp_joined_poly, mmu_fullPath)
                  
                print  mmu_copied_fc
                  
                fields = ["POLY_AREA" , "gridcode_1"]
                
                # implement the mmu criterion to the copied shape file, by deleting the rows
                # where the area <=100 m2 and they are not inside the stream network (gridcode_1 = 0)  
                with arcpy.da.UpdateCursor (mmu_copied_fc, fields) as cursor:
                    for row in cursor:        
                        if row[0]<=100 and row[1] < 1:
                            cursor.deleteRow()
                              

# Implement the mmu criterion by subtracting the water depth raster with the mmued polygons.                      
def extractbymask(mainDir):
    walk = arcpy.da.Walk(mainDir, topdown = True)
     
    for folderPath, folderNames, fileNames in walk:
         
        if 'CN' in folderPath:
            workspace = env.workspace = folderPath
             
            index = len(fileNames) - 1

            if fileNames[0].endswith('.tif'):
                Depth_Grid = arcpy.Raster(fileNames[0])
                 
            if fileNames[-1].endswith('_mmu.shp'):
                mmu_fc = fileNames[index]

                # Dissolve the mmu shape file 
                dis_name, file_extension = os.path.splitext(os.path.basename(mmu_fc)) 
                dis_name = dis_name + '_dis.shp'
                dis_fullPath = os.path.join(workspace,dis_name)                 
                dis_mmu_fc = arcpy.Dissolve_management(mmu_fc, dis_fullPath, "gridcode", "", "MULTI_PART", "DISSOLVE_LINES")
                 
                # extract by mask and also setting environment.
                final_raster_Name =  os.path.basename(workspace) + 'wD_mmu.tif'
                final_raster_fullpath = os.path.join(workspace, final_raster_Name)
                extract_by_mask = ExtractByMask(Depth_Grid, dis_mmu_fc)                 
                extract_by_mask.save(final_raster_fullpath)
                
                print final_raster_fullpath
                 
 

def main():
    binaryRaster = setnull(mainDir) 
    spJoin_polygon = polygon_processing(mainDir)
    mmu_polygon = mmu(mainDir)
    mmu_raster = extractbymask(mainDir)
    

if __name__ == "__main__":
    main()
    
arcpy.CheckInExtension('Spatial')    

elapsed_time = time.time() - start_time
print time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
