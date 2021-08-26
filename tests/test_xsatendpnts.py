"""Test getxsatendpts function."""
from tempfile import NamedTemporaryFile

import pytest

from nldi_xstool.nldi_xstool import getxsatendpts


@pytest.mark.parametrize(
    "path, numpts, crs, file, res",
    [
        (
            [(-107.077270, 39.643839), (-107.078088, 39.644977)],
            101,
            "epsg:4326",
            None,
            1,
        ),
        (
            [(-104.8195510, 40.116538), (-104.817563, 40.116721)],
            101,
            "epsg:4326",
            None,
            10,
        ),
        (
            [(-103.80097, 40.270568), (-103.801086, 40.267720)],
            101,
            "epsg:4326",
            None,
            1,
        ),
        ([(-96.168776, 39.064867), (-96.169119, 39.064497)], 101, "epsg:4326", None, 3),
    ],
)
def test_run_getxsatendpts(path, numpts, crs, file, res):
    """Test the getxsatendpts function.

    Args:
        path (list): List of lon lat tuples.
        numpts (int): Number of points in our cross-section.
        crs (str): EPSG string of lon lat values.
        file (str): path name of output file.
        res (float): Resolution of returned cross-section.
    """
    with NamedTemporaryFile(mode="w+") as tf:
        xs = getxsatendpts(path=path, numpts=numpts, crs=crs, file=tf, res=res)
        assert xs == 0
