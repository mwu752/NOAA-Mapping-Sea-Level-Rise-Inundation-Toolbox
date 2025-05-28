# NOAA-Mapping-Sea-Level-Rise-Inundation-Toolbox
This tool implements the mapping process developed by the NOAA Office for Coastal Management to visualize sea level rise inundation in the Sea Level Rise Viewer. The method follows a modified bathtub approach that incorporates local and regional tidal variability, as well as hydrological connectivity.

# 🌊 SLR Flood Modeling Toolbox

This ArcGIS Python Toolbox (`.pyt`) automates the generation of flood depth rasters for sea level rise (SLR) scenarios using a bathtub approach. It supports both fixed tidal elevation values and input raster surfaces, and optionally performs hydrological connectivity analysis.

## Overview

The tool is based on NOAA’s Sea Level Rise Viewer methodology and is designed for GIS analysts and coastal researchers to:

- Subtract DEM values from tidal surfaces
- Identify inundated areas
- Optionally isolate the largest hydrologically connected region

## Tool Name

**SLR Flood Depth Generator**

## ⚙Parameters

| Parameter | Type | Description |
|----------|------|-------------|
| `Input DEM` | Raster Layer | The Digital Elevation Model to be used for comparison against tidal surfaces. |
| `Use Raster Inputs for Tidal Surfaces?` | Boolean | If checked, use tidal surface rasters. If unchecked, use numeric values. |
| `Tidal Surface Elevation Values (feet)` | List of Double | Optional: Elevation values to subtract from the DEM. Ignored if raster inputs are used. |
| `Tidal Surface Raster(s)` | Raster Layer(s) | Optional: Raster(s) representing tidal elevations. Used if raster mode is enabled. |
| `Perform Connectivity Analysis` | Boolean | If checked, performs clumping and selects the largest connected flood zone (optional). |
| `Output Folder` | Folder | Directory where result rasters will be saved. |

## How It Works

Depending on the input type:

### 1. **Using Numeric Elevation Values**
- Creates a constant raster for each value
- Subtracts DEM from each constant surface
- Saves flood depth and optionally performs connectivity analysis

### 2. **Using Tidal Raster Inputs**
- Subtracts DEM from each tidal raster
- Saves flood depth and optionally performs connectivity analysis

If `Perform Connectivity Analysis` is checked:
- Identifies inundation extent
- Groups connected zones
- Extracts the largest flood zone
- Filters out areas < 1 acre (approx. 4800 cells for 10m DEMs)
- Outputs a masked flood depth raster for the connected region

## Output Files (per tidal surface)

Inside the output folder, each tidal surface will have a subfolder containing:
- `depth_<name>.tif` — Raw flood depth raster
- `extent_<name>.tif` — Binary extent of flooding
- `clumped_<name>.tif` — Region-grouped clumps
- `connect_<name>.tif` — Largest connected zone
- `lowlying_<name>.tif` — Areas larger than 1 acre
- `con_depth_<name>.tif` — Depth masked to connected zone

(*Only the first one is generated if connectivity is disabled.*)

## Notes

- Designed to work with projected DEMs in feet.
- Default acreage cutoff is based on 10m resolution (1 acre ≈ 4840 sq. yds).
- If your DEM is not 10m, adjust the pixel count threshold (`4800`) accordingly.
- Ensure Spatial Analyst extension is enabled.

## Citation / Attribution

This tool was developed based on NOAA’s Sea Level Rise Viewer mapping approach, incorporating elevation differencing and region grouping.

---


