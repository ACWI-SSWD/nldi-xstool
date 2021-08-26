"""Test getxsatpnt."""
from tempfile import NamedTemporaryFile

import pytest

from nldi_xstool.nldi_xstool import getxsatpoint


@pytest.mark.parametrize(
    "path, numpts, width, res",
    [
        ([-107.077270, 39.643839], 101, 1000, 1),
        ([-104.8195510, 40.116538], 101, 1000, 10),
        ([-103.80097, 40.270568], 101, 1000, 1),
        ([-96.168776, 39.064867], 101, 1000, 3),
    ],
)
def test_run_getxsatpoint(path, width, numpts, res):
    """Test getxsatpoint function."""
    with NamedTemporaryFile(mode="w+") as tf:
        xs = getxsatpoint(point=path, numpoints=numpts, width=width, file=tf, res=res)
        assert xs == 0
