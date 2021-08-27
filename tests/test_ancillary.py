"""Test get_ext_bathy_xs."""
import numpy.testing as npt
import pytest
from shapely.geometry import LineString
from shapely.geometry import Point

from nldi_xstool.ancillary import get_ext_bathy_xs
from nldi_xstool.ancillary import get_gage_datum
from nldi_xstool.ancillary import query_dems_shape


@pytest.mark.parametrize(
    "file, ext, lonstr, latstr, elstr, acrs",
    [
        (
            "./data/09152500_2019-10-25_bathymetry.csv",
            50,
            "Lon_NAD83",
            "Lat_NAD83",
            "Bed_Elevation_meters_NAVD88",
            "epsg:4326",
        )
    ],
)
def testxsbathy(file, ext, lonstr, latstr, elstr, acrs):
    """Test get_ext_bathy_xs function.

    Args:
        file (str): Path to example bathymetry cross-section file.
        ext (float): Extended distance on each side of original bathy cross-section.
        lonstr (str): String of heading used in bathy file to identify longitude column.
        latstr (str): String of heading used in bathy file to identify latitude column.
        elstr (str): String of heading used in bathy file to identify elevation column.
        acrs (str): EPSG code of in bathy file and returned extended cross-section.
    """
    xscomp = get_ext_bathy_xs(file, ext, lonstr, latstr, elstr, acrs)
    npt.assert_allclose(min(xscomp.elevation), 1410.657, rtol=1e-3, atol=0)
    npt.assert_allclose(max(xscomp.elevation), 1417.439, rtol=1e-3, atol=0)


@pytest.mark.parametrize(
    "gagenum, value",
    [
        ("02334480", 281.6352),
        ("02335350", 265.11504),
        ("02207055", 254.8128),
        ("03321350", 121.810272),
        ("06811500", 271.316),
    ],
)
def test_get_gage_datum(gagenum, value):
    """Test get_gage_datum function."""
    tval = get_gage_datum(gagenum=gagenum)
    npt.assert_almost_equal(tval, value, decimal=3)


@pytest.mark.parametrize(
    "path",
    [
        ([(-84.069592, 34.132959), (-84.070461, 34.131941)]),
        ([(-84.265284, 33.964690), (-84.264037, 33.965374)]),
        ([(-84.059534, 33.824598), (-84.058593, 33.825617)]),
        ([(-86.888014, 37.618517), (-86.887195, 37.619308)]),
        ([(-95.812660, 40.392760), (-95.814296, 40.392806)]),
    ],
)
def test_run_querydemoshap(path):
    """Test the query_dems_shape function."""
    linst = []
    for pt in path:
        linst.append(Point(pt[0], pt[1]))
    bbox = LineString(linst).envelope.bounds
    result = query_dems_shape(bbox=bbox)
    print(result)
