"""Main module."""
# from nldi_xstool.cli import xsatendpts
import sys

import geopandas as gpd
import numpy as np
import pandas as pd
import py3dep
import requests
from pynhd import NLDI
from shapely.geometry import LineString
from shapely.geometry import Point

from nldi_xstool.PathGen import PathGen
from nldi_xstool.XSGen import XSGen

# import json
# import xarray as xr
# from matplotlib import pyplot as plt

# import os.path as path


class HPoint(Point):  # noqa D101
    def __init__(self, *args, **kwargs):  # noqa D101
        super().__init__(*args, **kwargs)

    def __hash__(self):  # noqa D101
        return hash(tuple(self.coords))


def dataframe_to_geodataframe(df, crs):  # noqa D103
    geometry = [HPoint(xy) for xy in zip(df.x, df.y)]
    df = df.drop(["x", "y"], axis=1)
    gdf = gpd.GeoDataFrame(df, geometry=geometry, crs=crs)
    return gdf


def getxsatendpts(path, numpts, crs="epsg:4326", file=None, res=10):
    """Get cross-section at user-defined end points.

    Args:
        path (list): List containing end points of cross-sectin starting on river-left orientation, ie. viewed from
            downstream.
        numpts (int): Number of points in cross-section
        crs (str): CRS string of input path.
        file (str, optional): path and filename of returned cross-section as geojson file. Defaults to None.
        res (int): Resolution of topography used to generate cross-section.  Caution: underlying resolution by
            greater or less

    Returns:
        geopandas dataframe: returned cross-section as Geopandas DataFrame.
    """
    lnst = []
    for pt in path:
        # print(pt[0], pt[1])
        # x.append(pt[0])
        # y.append(pt[1])
        lnst.append(Point(pt[0], pt[1]))
    # ls1 = LineString(lnst)
    # print(ls1)
    d = {"name": ["xspath"], "geometry": [LineString(lnst)]}
    gpd_pth = gpd.GeoDataFrame(d, crs=crs)
    # print(gpd_pth)
    # gpd_pth.set_crs(epsg=4326, inplace=True)
    gpd_pth.to_crs(epsg=3857, inplace=True)
    # print(gpd_pth)
    xs = PathGen(path_geom=gpd_pth, ny=numpts)
    xs_line = xs.get_xs()
    # print(xs_line.head())
    # print(xs_line.total_bounds, xs_line.bounds)
    bb = xs_line.total_bounds - ((100.0, 100.0, -100.0, -100.0))
    # print('before dem', bb)
    dem = py3dep.get_map(
        "DEM", tuple(bb), resolution=res, geo_crs="EPSG:3857", crs="epsg:3857"
    )

    # print('after dem')
    x, y = xs.get_xs_points()
    dsi = dem.interp(x=("z", x), y=("z", y))
    x1 = dsi.coords["x"].values - dsi.coords["x"].values[0]
    y1 = dsi.coords["y"].values - dsi.coords["y"].values[0]
    dist = np.hypot(x1, y1)
    pdsi = dsi.to_dataframe()
    pdsi["distance"] = dist

    # gpdsi = gpd.GeoDataFrame(pdsi, gpd.points_from_xy(pdsi.x.values, pdsi.y.values))
    gpdsi = dataframe_to_geodataframe(pdsi, crs="epsg:3857")
    # gpdsi.set_crs(epsg=3857, inplace=True)
    gpdsi.to_crs(epsg=4326, inplace=True)
    if file:
        if not isinstance(file, str):
            # with open(file, "w") as f:
            file.write(gpdsi.to_json())
            file.close()
            return 0
        else:
            with open(file, "w") as f:
                f.write(gpdsi.to_json())
                f.close()
            # gpdsi.to_file(file, driver="GeoJSON")
            return 0
    else:
        return gpdsi


def getxsatpoint(point, numpoints, width, file=None, res=10):
    """Get cross-sectin given user defined point.

    Function uses USGS NLDI to find nearest stream-segment and intersection from given point.  The stream segment is
        interpolated using a tensioned spline and a cross-section is projected on to the resulting line given the user-
        defined width and numpoints.

    Args:
        point ([type]): [description]
        numpoints ([type]): [description]
        width ([type]): [description]
        file ([type], optional): [description]. Defaults to None.
        res (int, optional): [description]. Defaults to 10.

    Returns:
        [type]: [description]
    """
    # tpoint = f'POINT({point[1]} {point[0]})'
    df = pd.DataFrame(
        {"pointofinterest": ["this"], "Lat": [point[1]], "Lon": [point[0]]}
    )
    gpd_pt = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.Lon, df.Lat))
    gpd_pt.set_crs(epsg=4326, inplace=True)
    gpd_pt.to_crs(epsg=3857, inplace=True)
    try:
        comid = __get_cid_from_lonlat(point)
    except Exception as ex:
        # print(f'Error: {ex} unable to find comid - check lon lat coords')
        sys.exit(f"Error: {ex} unable to find comid - check lon lat coords")
    # print(f'comid = {comid}')
    strm_seg = NLDI().getfeature_byid("comid", comid).to_crs("epsg:3857")
    xs = XSGen(point=gpd_pt, cl_geom=strm_seg, ny=numpoints, width=width, tension=10.0)
    xs_line = xs.get_xs()
    # print(comid, xs_line)
    # get topo polygon with buffer to ensure there is enough topography to interpolate xs line
    # With coarsest DEM (30m) 100. m should
    bb = xs_line.total_bounds - ((100.0, 100.0, -100.0, -100.0))
    dem = py3dep.get_map(
        "DEM", tuple(bb), resolution=res, geo_crs="EPSG:3857", crs="epsg:3857"
    )
    x, y = xs.get_xs_points()
    dsi = dem.interp(x=("z", x), y=("z", y))
    x1 = dsi.coords["x"].values - dsi.coords["x"].values[0]
    y1 = dsi.coords["y"].values - dsi.coords["y"].values[0]
    dist = np.hypot(x1, y1)
    pdsi = dsi.to_dataframe()
    pdsi["distance"] = dist

    # gpdsi = gpd.GeoDataFrame(pdsi, gpd.points_from_xy(pdsi.x.values, pdsi.y.values))
    gpdsi = dataframe_to_geodataframe(pdsi, crs="epsg:3857")
    # gpdsi.set_crs(epsg=3857, inplace=True)
    gpdsi.to_crs(epsg=4326, inplace=True)
    if file:
        if not isinstance(file, str):
            # with open(file, "w") as f:
            file.write(gpdsi.to_json())
            file.close()
            return 0
        else:
            with open(file, "w") as f:
                f.write(gpdsi.to_json())
                f.close()
            # gpdsi.to_file(file, driver="GeoJSON")
            return 0
    else:
        return gpdsi


def __lonlat_to_point(lon, lat):  # noqa D103
    return Point(lon, lat)


def __get_cid_from_lonlat(point):
    # print(point)
    pt = __lonlat_to_point(point[0], point[1])
    location = pt.wkt
    location = f"POINT({point[0]} {point[1]})"
    base_url = "https://labs.waterdata.usgs.gov/api/nldi/linked-data/comid/position?f=json&coords="
    url = base_url + location
    # print(url)
    try:
        response = requests.get(url)
        # print(f'this is the response: {response}')
        response.raise_for_status()
        jres = response.json()
        comid = jres["features"][0]["properties"]["comid"]
        return comid
    except requests.exceptions.RequestException as err:
        print("OOps: Something Else", err)
    except requests.exceptions.HTTPError as errh:
        print("Http Error:", errh)
    except requests.exceptions.ConnectionError as errc:
        print("Error Connecting:", errc)
    except requests.exceptions.Timeout as errt:
        print("Timeout Error:", errt)
    except Exception as ex:
        raise ex
