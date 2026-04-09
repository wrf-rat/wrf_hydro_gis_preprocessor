import argparse
import os
import math
import yaml
import netCDF4
import numpy as np
import elevatr as elev


def load_config(config_path):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def get_domain_extent(geo_em_path, buffer_deg=0.5):
    ds = netCDF4.Dataset(geo_em_path, "r")
    ds.set_auto_mask(False)
    lat = ds.variables["XLAT_M"][0, :, :]
    lon = ds.variables["XLONG_M"][0, :, :]
    ds.close()

    west = float(np.min(lon)) - buffer_deg
    east = float(np.max(lon)) + buffer_deg
    south = float(np.min(lat)) - buffer_deg
    north = float(np.max(lat)) + buffer_deg
    return (west, south, east, north)


def download_dem(bbox, zoom, output_path, cache_dir):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    os.makedirs(cache_dir, exist_ok=True)

    print(f"Preparing DEM at zoom level {zoom}...")
    raster = elev.get_elev_raster(
        locations=bbox,
        zoom=zoom,
        crs="EPSG:4326",
        clip="bbox",
        cache_folder=cache_dir,
        use_cache=True,
        delete_cache=True, # Delete cached tiles after creating DEM
        verbose=True,
    )

    print(f"  Raster size: {raster.width} x {raster.height} pixels")
    print(f"  Sources: {raster.imagery_sources}")

    # Print DEM resolution in degrees
    res = raster.resolution
    dx_deg = res["x"]
    dy_deg = res["y"]
    print(f"  Resolution: {dx_deg:.6f} x {dy_deg:.6f} deg")

    # Remove 'bounds' from meta
    raster.meta.pop("bounds", None)
    raster.to_tif(output_path, compress="lzw")

    print(f"  DEM saved to {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Download DEM for WRF-HYDRO domain")
    parser.add_argument("config", help="Path to config file")
    args = parser.parse_args()
    config = load_config(args.config)

    geo_em_path = config["paths"]["geo_em"]
    dem_config = config["dem_download"]

    print("Extracting domain extent from geo_em file...")
    bbox = get_domain_extent(geo_em_path, dem_config["buffer_deg"])
    print(f"  Bounding box (W, S, E, N): {bbox}")

    output_dir = dem_config["output_dir"]
    output_path = os.path.join(output_dir, "dem.tif")
    cache_dir = os.path.join(output_dir, "dem_cache")

    download_dem(bbox, dem_config["zoom"], output_path, cache_dir)


if __name__ == "__main__":
    main()
