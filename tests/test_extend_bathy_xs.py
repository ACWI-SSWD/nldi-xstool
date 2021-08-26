"""Test get_ext_bathy_xs."""
import numpy.testing as npt
import pytest

from nldi_xstool.ancillary import get_ext_bathy_xs


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
