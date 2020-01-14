# -*- coding: utf-8 -*-
# importing modules
import os,sys
import arcpy 
from arcpy import env
from arcpy.sa import *


arcpy.CheckOutExtension("Spatial")
arcpy.CheckOutExtension("3D")
arcpy.env.overwriteOutput = True


mainDir = r'D:\mandra'
streams = r'D:\mandra\HN\streams.shp'

print mainDir

walk = arcpy.da.Walk(mainDir, topdown = True, datatype = 'RasterDataset') # define the raster data type, the script will access.

# Setnull the initial Raster with the water depths in order to convert it later to polygon
for folderPath, folderNames, fileNames in walk:
       
    if 'CN' in folderPath:
        workspace = env.workspace = folderPath
         
        depth_outGrid_Name = os.path.basename(workspace) + '_stnull.tif'
        depth_outGrid_fullPath = os.path.join(workspace, depth_outGrid_Name)
           
        print depth_outGrid_fullPath
           
        if fileNames[0].endswith('.tif'):
            Depth_Grid = arcpy.Raster(fileNames[0])
               
            print (Depth_Grid)
                           
            setNull_Depth_Grid = SetNull(Depth_Grid, 1, "VALUE < 0")
               
            setNull_Depth_Grid.save(depth_outGrid_fullPath)
                
          
#  Convert Set null Raster to polygon

for folderPath, folderNames, fileNames in walk:
     
    if 'CN' in folderPath:
        workspace = env.workspace = folderPath
         
        # The fileNames variable in fact is a list with the name of the rasters that exist inside each folder. Every time we create a new raster the list's length grows
        # per one. So, we create the index variable in order to be able to manipulate dynamically the newest raster. 
          
        index = len(fileNames) - 1
         
        if fileNames[index].endswith('_stnull.tif'):
            
            stNull_Grid = arcpy.Raster(fileNames[index])
            
            polygon_Name = os.path.basename(workspace) + 'poly.shp'
            polygon_fullPath = os.path.join(workspace, polygon_Name)
             
            polygon_Depth = arcpy.RasterToPolygon_conversion(stNull_Grid, polygon_fullPath, "NO_SIMPLIFY", "VALUE") # convert raster to polygon
             
         
            # Calculate polygon area in squared meters.
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
             
            print (SpatialJoin_with_Streams)
             
 
walk2 = arcpy.da.Walk(mainDir, topdown = True, datatype = 'FeatureClass') 
 
print walk2
            
for folderPath, folderNames, fileNames in walk2:
     
    print folderPath, folderNames, fileNames
     
    if 'CN' in folderPath:
        workspace = env.workspace = folderPath
         
        index = len(fileNames) - 1
     
        if fileNames[index].endswith('_SpJoin.shp'):
            Sp_joined_poly = fileNames[index]
             
            print Sp_joined_poly
             
            mmu_name = os.path.basename(workspace) + '_mmu.shp'
            mmu_fullPath = os.path.join(workspace, mmu_name)
             
             
             
            mmu_copied_feature = arcpy.CopyFeatures_management(Sp_joined_poly, mmu_fullPath)
             
            print  mmu_copied_feature
             
            fields = ["POLY_AREA" , "gridcode_1"]
             
            with arcpy.da.UpdateCursor (mmu_copied_feature, fields) as cursor:
                for row in cursor:        
                    if row[0]<=100 and row[1] < 1:
                        cursor.deleteRow()
                         
                        print (row[0], row[1])
                     


walk3 = arcpy.da.Walk(mainDir, topdown = True) 

for folderPath, folderNames, fileNames in walk3:
    
    #print folderPath, folderNames, fileNames
    
    if 'CN' in folderPath:
        workspace = env.workspace = folderPath
        
        print fileNames
        
        index = len(fileNames) - 1
        
        print index
        
        if fileNames[0].endswith('.tif'):
            Depth_Grid = arcpy.Raster(fileNames[0])
            
            print Depth_Grid
            
        if fileNames[-1].endswith('_mmu.shp'):
            mmu_fc = fileNames[index]
                       
            print mmu_fc 

            # Dissolve the mmu shape file 
            dis_name, file_extension = os.path.splitext(os.path.basename(mmu_fc)) 
            dis_name = dis_name + '_dis.shp'
            dis_fullPath = os.path.join(workspace,dis_name) 
            
            
            dis_mmu_fc = arcpy.Dissolve_management(mmu_fc, dis_fullPath, "gridcode", "", "MULTI_PART", "DISSOLVE_LINES")
            
            
            # extract by mask and also setting environment.
            
            final_raster_Name =  os.path.basename(workspace) + 'wD_mmu.tif'
            final_raster_fullpath = os.path.join(workspace, final_raster_Name)
            
            print final_raster_fullpath
            
           
            extract_by_mask = ExtractByMask(Depth_Grid, dis_mmu_fc)
            
            print (extract_by_mask) 
            
            extract_by_mask.save(final_raster_fullpath)
            
      
arcpy.CheckInExtension('Spatial')            
            
            
            
            
            
            
            
            
        


        
        
        
        
        
    
        
        
    
