# -*- coding: utf-8 -*-

import arcpy
import os
from arcpy.sa import *

class Toolbox:
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "SLR Flood Modeling Toolbox"
        self.alias = "slr_flood"

        # List of tool classes associated with this toolbox
        self.tools = [FloodTool]


class FloodTool:
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "SLR Flood Depth Generator"
        self.description = "Generates flood depth rasters for multiple tidal surface elevations"
        self.canRunInBackground = True

    def getParameterInfo(self):
        """Define the tool parameters."""
        params = []

        # Input DEM
        param0 = arcpy.Parameter(
            displayName="Input DEM",
            name="dem",
            datatype="GPRasterLayer",
            parameterType="Required",
            direction="Input"
        )

        # Toggle: Use raster inputs instead of numeric values
        param1 = arcpy.Parameter(
            displayName="Use Raster Inputs for Tidal Surfaces?",
            name="use_raster",
            datatype="Boolean",
            parameterType="Required",
            direction="Input"
        )
        param1.value = False

        # Tidal surface values (MultiValue Double)
        param2 = arcpy.Parameter(
            displayName="Tidal Surface Elevation Values (feet)",
            name="tidal_values",
            datatype="Double",
            parameterType="Optional",
            direction="Input",
            multiValue=True
        )

        # Tidal surface rasters (MultiValue Raster Layer)
        param3 = arcpy.Parameter(
            displayName="Tidal Surface Raster(s)",
            name="tidal_rasters",
            datatype="GPRasterLayer",
            parameterType="Optional",
            direction="Input",
            multiValue=True
        )

        # Perform Connectivity Analysis (not used yet)
        param4 = arcpy.Parameter(
            displayName="Perform Connectivity Analysis",
            name="perform_connective",
            datatype="Boolean",
            parameterType="Required",
            direction="Input"
        )
        param4.value = False

        # Output folder
        param5 = arcpy.Parameter(
            displayName="Output Folder",
            name="output_folder",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input"
        )

        return [param0, param1, param2, param3, param4, param5]
        

    def isLicensed(self):
        """Set whether the tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        use_raster = parameters[1].value

        if use_raster:
            parameters[2].enabled = False  # Disable numeric input
            parameters[3].enabled = True   # Enable raster input
        else:
            parameters[2].enabled = True
            parameters[3].enabled = False

        return
        

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter. This method is called after internal validation."""
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        arcpy.CheckOutExtension("Spatial")

        dem = arcpy.Raster(parameters[0].valueAsText)
        use_raster = parameters[1].value
        perform_connective = parameters[4].value
        output_folder = parameters[5].valueAsText

        arcpy.env.extent = dem.extent
        arcpy.env.cellSize = dem.meanCellWidth
        arcpy.env.snapRaster = dem
        arcpy.env.outputCoordinateSystem = dem.spatialReference

        def process_surface(tidal_raster, base_name):
            subfolder = os.path.join(output_folder, base_name)
            os.makedirs(subfolder, exist_ok=True)
            messages.addMessage(f"Processing surface: {base_name}")

            flood_depth = Con(dem <= tidal_raster, tidal_raster - dem)
            flood_depth.save(os.path.join(subfolder, f"depth_{base_name}.tif"))

            if not perform_connective:
                messages.addMessage(f"Saved: flood_depth_{base_name}.tif")
                return

            # Step 3: extent
            single_x = Con(dem <= tidal_raster, 1)
            single_x.save(os.path.join(subfolder, f"extent_{base_name}.tif"))

            # Step 4: region group
            clumped_x = RegionGroup(single_x, "EIGHT", "WITHIN", "NO_LINK")
            clumped_path = os.path.join(subfolder, f"clumped_{base_name}.tif")
            clumped_x.save(clumped_path)

            arcpy.management.BuildRasterAttributeTable(clumped_path, "Overwrite")
            arcpy.management.CalculateStatistics(clumped_path)

            # Step 5: get largest connected zone
            max_zone = None
            max_count = -1
            with arcpy.da.SearchCursor(clumped_path, ["Value", "Count"]) as cursor:
                for val, count in cursor:
                    if count > max_count:
                        max_zone = val
                        max_count = count

            connect_x = ExtractByAttributes(clumped_path, f'"Value" = {max_zone}')
            connect_x.save(os.path.join(subfolder, f"connect_{base_name}.tif"))

            # Step 6: low-lying > 1 acre
            lowlying_x = ExtractByAttributes(clumped_path, '"Count" > 4800')  # Adjust if cell size is not 10m
            lowlying_x.save(os.path.join(subfolder, f"lowlying_{base_name}.tif"))

            # Step 7: mask flood depth to connected region
            con_depth_x = ExtractByMask(flood_depth, connect_x)
            con_depth_x.save(os.path.join(subfolder, f"con_depth_{base_name}.tif"))

            messages.addMessage(f"Connectivity analysis complete for {base_name}")

        if use_raster:
            for raster in parameters[3].values:
                tidal_raster = arcpy.Raster(raster)
                base_name = os.path.splitext(os.path.basename(raster))[0]
                process_surface(tidal_raster, base_name)
        else:
            for tidal_value in parameters[2].values:
                base_name = f"{float(tidal_value):.2f}ft"
                raw_constant = CreateConstantRaster(float(tidal_value), "FLOAT", dem.meanCellWidth, dem.extent)
                masked_constant = Con(IsNull(dem) == 0, raw_constant)
                process_surface(masked_constant, base_name)

        arcpy.CheckInExtension("Spatial")
        return

    def postExecute(self, parameters):
        """This method takes place after outputs are processed and
        added to the display."""
        return
