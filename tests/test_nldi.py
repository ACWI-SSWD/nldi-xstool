"""Tests of NLDI functions used in processes."""
import pytest
from numpy import array
from numpy.testing import assert_allclose
from pynhd import NLDI

# from shapely.geometry import Point


@pytest.mark.parametrize(
    "gage, loc, comid",
    [
        ("USGS-06888500", [(-10705502.110, 4730946.304)], "3643688"),
        ("USGS-06721000", [(-11668351.314, 4882827.631)], "225621"),
        ("USGS-06759500", [(-11555095.784, 4905023.218)], "3561878"),
    ],
)
def test_nldi(gage, loc, comid):
    """Test nldi functions used in processes.

    Args:
        gage (string): USGS Gage id string.
        loc (list): List of lon and lat
        comid (str): Expected comid returned from NLDI query.
    """
    locarray = array(loc)
    gageloc = NLDI().getfeature_byid("nwissite", gage).to_crs("epsg:3857")
    cid = gageloc.comid.values.astype(str)
    strmseg_loc = NLDI().getfeature_byid("comid", cid[0]).to_crs("epsg:3857")
    print(strmseg_loc.comid[0])
    assert strmseg_loc.comid[0] == comid
    gageloc_array = array([(gageloc.geometry[0].x, gageloc.geometry[0].y)])
    assert_allclose(gageloc_array, locarray, rtol=0.1)
