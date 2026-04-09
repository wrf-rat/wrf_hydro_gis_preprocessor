import argparse
import os
import copy
import shutil
import yaml
import netCDF4

from wrfhydro_gis.wrfhydro_functions import WRF_Hydro_Grid, ZipCompat
from wrfhydro_gis.Build_GeoTiff_From_Geogrid_File import build_geogrid_raster
from wrfhydro_gis.Build_Routing_Stack import GEOGRID_STANDALONE, varList2D
from wrfhydro_gis.Examine_Outputs_of_GIS_Preprocessor import examine_outputs


def load_config(config_path):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def main():
    parser = argparse.ArgumentParser(description="NCAR WRF-HYDRO GIS Preprocessor")
    parser.add_argument("config", help="Path to the YAML configuration file")
    args = parser.parse_args()
    config = load_config(args.config)

    paths = config["paths"]
    stack = config["routing_stack"]
    opsteps = config["optional_steps"]

    geo_em = paths["geo_em"]
    output_dir = paths["output_dir"]
    dem = os.path.join(output_dir, "dem.tif")

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    print(f"Output directory: {output_dir}")

    # Optionally: Create domain boundary shapefile
    if opsteps["create_boundary_shapefile"]:
        print("Creating domain boundary shapefile...")
        out_shp = os.path.join(output_dir, os.path.basename(geo_em).replace(".nc", "_boundary.shp"))
        rootgrp = netCDF4.Dataset(geo_em, "r")
        grid = WRF_Hydro_Grid(rootgrp)
        grid.boundarySHP(out_shp, "ESRI Shapefile")
        rootgrp.close()
        print(f"  Boundary shapefile: {out_shp}")

    # Optionally: Build GeoTIFF from geogrid variable
    if opsteps["build_geotiff"]:
        variable = opsteps["geotiff_variable"]
        out_tif = os.path.join(output_dir, f"{variable}.tif")
        print(f"Building GeoTIFF for variable '{variable}'...")
        build_geogrid_raster(geo_em, variable, out_tif)

    # Build routing stack
    print("Building routing stack...")
    projdir = os.path.join(output_dir, "scratchdir")
    if os.path.exists(projdir):
        shutil.rmtree(projdir)
    os.makedirs(projdir)

    GEOGRID_STANDALONE(
        inGeogrid=geo_em,
        regridFactor=stack["regrid_factor"],
        inDEM=dem,
        projdir=projdir,
        threshold=stack["threshold"],
        out_zip=paths["output_zip"],
        in_csv=paths.get("streamgages_csv") or "",
        basin_mask=stack["basin_mask"],
        routing=stack["routing"],
        varList2D=copy.deepcopy(varList2D),
        in_lakes=paths.get("lakes_shapefile") or "",
        GW_with_Stack=stack["gw_with_stack"],
        in_GWPolys=paths.get("gw_polys"),
        ovroughrtfac_val=stack["ovroughrtfac_val"],
        retdeprtfac_val=stack["retdeprtfac_val"],
        lksatfac_val=stack["lksatfac_val"],
        startPts=paths.get("channel_starts"),
        channel_mask=paths.get("channel_mask"),
    )

    # Optionally: Examine outputs
    if opsteps["examine_outputs"]:
        print("Examining outputs...")
        ZipCompat(paths["output_zip"]).extractall(output_dir)
        examine_outputs(output_dir)


if __name__ == "__main__":
    main()
