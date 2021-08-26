"""Test nldi-xstool packages."""
import json

import py3dep
import pytest
from pynhd import NLDI

from nldi_xstool.ancillary import query_dems_shape
from nldi_xstool.XSGen import XSGen


@pytest.mark.parametrize(
    "gage, gage_name, res, ny, width",
    [
        ("USGS-06888500", "MILL C NR PAXICO, KS", 3, 100, 200),
        ("USGS-06721000", "SOUTH PLATTE RIVER AT FORT LUPTON, CO.", 10, 100, 200),
        ("USGS-06759500", "SOUTH PLATTE RIVER AT FORT MORGAN, CO.", 1, 100, 200),
    ],
)
def test_get_gagexs(gage, gage_name, res, ny, width):
    """Test XSGen class and packages required to generate cross-section.

    Args:
        gage (str): USGS Gage idientifier: USGS-XXXXXXXX
        gage_name (str): Gage name
        res (int): 3DEP DEM interpolated to resolution res
        ny (int): Number of points in cross-section
        width (float): Width of cross-section
    """
    gageloc = NLDI().getfeature_byid("nwissite", gage).to_crs("epsg:3857")
    cid = gageloc.comid.values.astype(str)
    # print(cid, gageloc.comid.values.astype(int)[0])
    strmseg_loc = NLDI().getfeature_byid("comid", cid[0]).to_crs("epsg:3857")
    xs = XSGen(point=gageloc, cl_geom=strmseg_loc, ny=ny, width=width)
    xs_line = xs.get_xs()
    spline = xs.get_strm_seg_spline()
    print(spline)
    t1 = (xs_line.total_bounds) + ((-100.0, -100.0, 100.0, 100.0))
    xs_line_geom = xs_line.to_crs("epsg:4326")
    bbox = xs_line_geom.geometry[0].envelope.bounds
    query = query_dems_shape(bbox)
    # print(query)
    query_text = json.dumps(query)
    print(query_text)

    x, y = xs.get_xs_points()
    dem = py3dep.get_map(
        "DEM", tuple(t1), resolution=res, geo_crs="EPSG:3857", crs="epsg:3857"
    )
    dsi = dem.interp(x=("z", x), y=("z", y))
    vals = dsi.values
    if ny % 2 == 0:
        ny += 1

    assert len(vals) == ny
    assert vals.dtype == float
