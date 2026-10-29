"""Create a raster-cell fishnet as a GeoPackage. Requires rasterio, fiona, shapely.
Usage: python create_fishnet.py input.tif output.gpkg --chunk-rows 50
"""
import argparse
from pathlib import Path
import rasterio
import fiona
from shapely.geometry import Polygon, mapping


def cell_polygon(transform, row, col):
    corners = [transform * (col, row), transform * (col+1, row),
               transform * (col+1, row+1), transform * (col, row+1)]
    return Polygon(corners)


def create_fishnet(raster_path, output_path, chunk_rows=50):
    if chunk_rows < 1:
        raise ValueError('chunk_rows must be positive')
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        raise FileExistsError(output_path)
    with rasterio.open(raster_path) as ds:
        if ds.crs is None:
            raise ValueError('Raster has no CRS')
        if ds.transform.is_degenerate:
            raise ValueError('Degenerate raster transform')
        schema = {'geometry': 'Polygon', 'properties': {'cell_id': 'int'}}
        with fiona.open(output_path, 'w', driver='GPKG', crs_wkt=ds.crs.to_wkt(), schema=schema) as dst:
            for start in range(0, ds.height, chunk_rows):
                for row in range(start, min(start+chunk_rows, ds.height)):
                    for col in range(ds.width):
                        poly = cell_polygon(ds.transform, row, col)
                        dst.write({'geometry': mapping(poly),
                                   'properties': {'cell_id': row*ds.width+col+1}})
    return output_path


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('raster')
    p.add_argument('output')
    p.add_argument('--chunk-rows', type=int, default=50)
    a = p.parse_args()
    print(create_fishnet(a.raster, a.output, a.chunk_rows))
