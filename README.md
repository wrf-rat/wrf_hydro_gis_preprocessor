# WRF-Hydro GIS Preprocessor

A two-stage toolkit for preparing geospatial inputs for [NCAR WRF-Hydro](https://ral.ucar.edu/projects/wrf_hydro) hydrological simulations. It automates DEM acquisition and the generation of routing grids, terrain files, and diagnostic outputs from a WRF geogrid (`geo_em`) file.

## Workflow

```
geo_em.d01.nc ──► prepare_dem.py ──► dem.tif ──► gis_preprocess.py ──► routing grids (ZIP)
```

Both scripts are driven by a single shared configuration file (`wrfhydro_gis_config.yaml`).

---

## Files

### `prepare_dem.py` — DEM Download

Downloads a Digital Elevation Model covering the WRF domain.

1. **Reads the `geo_em` file** to extract the model domain's latitude/longitude extent.
2. **Buffers the bounding box** (default 0.5°) to ensure full coverage beyond domain edges.
3. **Fetches elevation tiles** via the [`elevatr`](https://github.com/earth-chris/elevatr) library at a configurable zoom level (0–14).
4. **Writes a compressed GeoTIFF** (`dem.tif`) to the output directory.

Key config keys (`dem_download`): `zoom`, `buffer_deg`, `output_dir`.

### `gis_preprocess.py` — Routing Stack & Diagnostics

Runs the core NCAR `wrfhydro_gis` processing chain to produce all hydrological routing grids.

1. **(Optional) Boundary shapefile** — exports the geogrid domain outline as an ESRI Shapefile.
2. **(Optional) GeoTIFF export** — rasterises a selected geogrid variable (e.g. `HGT_M`) for inspection.
3. **Routing stack** — calls `GEOGRID_STANDALONE` to regrid the DEM, delineate channels, and build the full suite of WRF-Hydro routing files (flow direction, channel grid, lake parameters, groundwater polygons, etc.). Results are packaged into a ZIP archive.
4. **(Optional) Output examination** — extracts the ZIP and runs `examine_outputs` to generate diagnostic plots and summaries.

Key config sections: `paths`, `routing_stack`, `optional_steps`.

### `wrfhydro_gis_config.yaml` — Configuration

Single YAML file shared by both scripts. Sections include:

| Section | Purpose |
|---|---|
| `paths` | Input/output file locations (`geo_em`, output directory, optional shapefiles/CSVs) |
| `routing_stack` | Regrid factor, stream threshold, basin/routing flags, surface-parameter scaling factors |
| `optional_steps` | Toggle boundary shapefile, GeoTIFF export, and output examination |
| `dem_download` | Zoom level, bounding-box buffer, and output directory for `prepare_dem.py` |

### `environment.yml` — Conda Environment

Defines the `wrfh_gis_env` conda environment (Python 3.10) with all required dependencies: GDAL, NetCDF4, Rasterio, WhiteBox, GeoPandas, Cartopy, and the pip-installed `elevatr` package.

---

## Quick Start

```bash
# 1. Create and activate the environment
conda env create -f environment.yml
conda activate wrfh_gis_env

# 2. Edit wrfhydro_gis_config.yaml to set your paths and parameters

# 3. Download the DEM
python prepare_dem.py wrfhydro_gis_config.yaml

# 4. Run the GIS preprocessor
python gis_preprocess.py wrfhydro_gis_config.yaml
```

## Requirements

- Python 3.10
- A valid WRF `geo_em.d01.nc` geogrid file (produced by WPS)
- Internet access for DEM tile downloads (Step 3)
- NCAR `wrfhydro_gis` package installed in the environment