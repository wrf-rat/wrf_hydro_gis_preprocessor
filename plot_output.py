import argparse
import os
import glob
import yaml
import numpy as np
import matplotlib.pyplot as plt
import rasterio


def load_config(config_path):
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


# (colormap, log_scale)
PLOT_CONFIG = {
    "TOPOGRAPHY":    ("terrain", False),
    "FLOWDIRECTION": ("twilight", False),
    "FLOWACC":       ("Blues", True),
    "STREAMORDER":   ("YlGnBu", False),
    "CHANNELGRID":   ("binary_r", False),
    "LAKEGRID":      ("cool", False),
    "basn_msk":      ("Set2", False),
    "BASIN":         ("tab20", False),
    "frxst_pts":     ("Reds", False),
    "landuse":       ("tab20", False),
    "OVROUGHRTFAC":  ("YlOrBr", False),
    "RETDEPRTFAC":   ("YlOrBr", False),
    "LKSATFAC":      ("YlOrBr", False),
    "LATITUDE":      ("RdYlBu_r", False),
    "LONGITUDE":     ("RdYlBu", False),
}


def plot_raster(tif_path, out_png, cmap, log_scale):
    with rasterio.open(tif_path) as src:
        data = src.read(1).astype(float)
        nodata = src.nodata
        bounds = src.bounds

    if nodata is not None:
        data = np.ma.masked_equal(data, nodata)
    data = np.ma.masked_where(np.isnan(data), data)

    if data.count() == 0:
        print(f"  Skipping {os.path.basename(tif_path)} (all nodata)")
        return

    name = os.path.splitext(os.path.basename(tif_path))[0]
    label = name

    if log_scale:
        data = np.ma.log10(np.ma.clip(data, 1, None))
        label = f"log10({name})"

    extent = [bounds.left, bounds.right, bounds.bottom, bounds.top]

    fig, ax = plt.subplots(figsize=(10, 8))
    im = ax.imshow(data, cmap=cmap, extent=extent, aspect="equal")
    ax.set_title(name)
    fig.colorbar(im, ax=ax, shrink=0.7, label=label)
    fig.savefig(out_png, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  Saved: {out_png}")


def main():
    parser = argparse.ArgumentParser(description="Plot WRF-Hydro GIS Preprocessor outputs")
    parser.add_argument("config", help="Path to the YAML configuration file")
    args = parser.parse_args()
    config = load_config(args.config)

    output_dir = config["paths"]["output_dir"]
    plot_dir = os.path.join(output_dir, "plots")
    os.makedirs(plot_dir, exist_ok=True)

    tif_files = sorted(glob.glob(os.path.join(output_dir, "*.tif")))
    print(f"Found {len(tif_files)} GeoTIFF files in {output_dir}")

    for tif_path in tif_files:
        stem = os.path.splitext(os.path.basename(tif_path))[0]
        cmap, log_scale = PLOT_CONFIG.get(stem, ("viridis", False))
        out_png = os.path.join(plot_dir, f"{stem}.png")
        plot_raster(tif_path, out_png, cmap, log_scale)

    print(f"Done. Plots saved to {plot_dir}")


if __name__ == "__main__":
    main()
