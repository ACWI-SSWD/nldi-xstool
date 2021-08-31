"""Command-line interface."""
import sys
from typing import Any
from typing import Tuple

import click
import shapely

from .nldi_xstool import getxsatendpts
from .nldi_xstool import getxsatpoint

# 3dep resolution
resdict = {"1m": 1, "3m": 3, "5m": 5, "10m": 10, "30m": 30, "60m": 60}

# from:
# https://gis.stackexchange.com/questions/363221/how-do-you-validate-longitude-and-latitude-coordinates-in-python/378885#378885


def valid_lonlat(ctx: Any, param: Any, value: Any) -> tuple[float, ...]:
    """This validates a lat and lon.

    This validates a lat and lonpoint can be located
    in the bounds of the WGS84 CRS, after wrapping the
    longitude value within [-180, 180).

    :param lon: a longitude value
    :param lat: a latitude value
    :return: (lon, lat) if valid, None otherwise
    """
    print(f"latlon: {param, value}")
    assert len(value) == 2
    lon = float(value[0])
    lat = float(value[1])
    # Put the longitude in the range of [0,360):
    lon %= 360
    # Put the longitude in the range of [-180,180):
    if lon >= 180:
        lon -= 360
    lon_lat_point = shapely.geometry.Point(lon, lat)
    lon_lat_bounds = shapely.geometry.Polygon.from_bounds(
        xmin=-180.0, ymin=-90.0, xmax=180.0, ymax=90.0
    )
    # return lon_lat_bounds.intersects(lon_lat_point)
    # would not provide any corrected values
    try:
        if lon_lat_bounds.intersects(lon_lat_point):
            retval = tuple((lon, lat))
            # return lon, lat
    except ValueError:
        msg = f"Not valid lon lat pair: {lon, lat}"
        raise click.BadParameter(msg)
    return retval


class NLDIXSTool:
    """Simple class to handle global crs."""

    def __init__(self: "NLDIXSTool") -> None:
        """Init NLDIXSTool."""
        self.out_crs = "epsg:4326"

    def setoutcrs(self: "NLDIXSTool", out_crs: str = "epsg:4326") -> None:
        """Set the CRS for output.

        Args:
            out_crs (str): Set the CRS string for projection of output. Defaults to "epsg:4326".
        """
        self.out_crs = out_crs

    def outcrs(self: "NLDIXSTool") -> str:
        """Get the output CRS.

        Returns:
            str: The epsg crs code.
        """
        return self.out_crs

    def __repr__(self: "NLDIXSTool") -> str:
        """Representation.

        Returns:
            str: Representation ouput.
        """
        return f"NLDI_XSTool {self.out_crs}"


pass_nldi_xstool = click.make_pass_decorator(NLDIXSTool)


@click.group()
@click.option(
    "--outcrs",
    default="epsg:4326",
    help="Projection CRS to return cross-section geometry: default is epsg:4326",
)
@click.version_option("0.1")
@click.pass_context
def main(ctx: Any, outcrs: str) -> int:
    """nldi-xstooln is a command line tool to for elevation-based services to the NLDI."""
    ctx.obj = NLDIXSTool()
    ctx.obj.setoutcrs(outcrs)
    return 0


# XS command at point with NHD


@main.command()
@click.option(
    "-f",
    "--file",
    default=None,
    type=click.File("w"),
    help="enter path and filenmae for json ouput",
)
@click.option(
    "-ll",
    "--lonlat",
    required=True,
    # type=valid_lonlat(float, float),
    type=tuple((float, float)),
    callback=valid_lonlat,
    help="format lon,lat (x,y) as floats for example: -103.8011 40.2684",
)
@click.option(
    "-n", "--numpoints", default=101, type=int, help="number of points in cross-section"
)
@click.option(
    "-w", "--width", default=1000.0, type=float, help="width of cross-section"
)
@click.option(
    "-r",
    "--resolution",
    type=click.Choice(["1m", "3m", "5m", "10m", "30m", "60m"], case_sensitive=False),
    default="10m",
    help="Resolution of DEM used.  Note: 3DEP provides server side interpolatin given best available data",
)
@click.option("-v", "--verbose", default=False, type=bool, help="verbose ouput")
@pass_nldi_xstool
def xsatpoint(
    nldi_xstool: "NLDIXSTool",
    lonlat: Tuple[float, float],
    numpoints: int,
    width: float,
    resolution: str,
    file: Any,
    verbose: bool,
) -> int:
    """[summary].

    Parameters
    ----------
    nldi_xstool : NLDIXSTool
        [description]
    lonlat : Tuple[float, float]
        [description]
    numpoints : int
        [description]
    width : float
        [description]
    resolution : str
        [description]
    file : Any
        [description]
    verbose : bool
        [description]

    Returns
    -------
    [type]
        [description]
    """
    coord = []
    coord.append(lonlat[0])
    coord.append(lonlat[1])
    x = lonlat[0]  # noqa DAR003
    y = lonlat[1]
    nl = "\n"
    if verbose:
        print(
            f"input={lonlat}, lat={x}, lon={y}, {nl} \
                npts={numpoints}, width={width}, resolution={resolution}, {nl} \
                crs={nldi_xstool.outcrs()}, {nl} \
                file={file}, {nl} \
                out_epsg={nldi_xstool.outcrs()}"
        )
    # print(tuple(latlon))
    xs = getxsatpoint(
        point=coord,
        numpoints=numpoints,
        width=width,
        file=file,
        res=resdict.get(resolution),
    )
    if file is None:
        print(xs.to_json())
    return 0


# XS command at user defined endpoints


@main.command()
@click.option(
    "-f", "--file", default=None, type=click.File("w"), help="Output json file"
)
@click.option(
    "-s",
    "--startpt",
    required=True,
    type=tuple((float, float)),
    help="format x y pair as floats for example: -103.801134 40.267335",
)
@click.option(
    "-e",
    "--endpt",
    required=True,
    type=tuple((float, float)),
    help="format x y pair as floats for example: -103.800787 40.272798 ",
)
@click.option(
    "-c",
    "--crs",
    required=True,
    type=str,
    help="spatial reference of input data",
    default="epsg:4326",
)
@click.option(
    "-n", "--numpoints", default=100, type=int, help="number of points in cross-section"
)
@click.option(
    "-r",
    "--resolution",
    type=click.Choice(["1m", "3m", "5m", "10m", "30m", "60m"], case_sensitive=False),
    default="10m",
    help="Resolution of DEM used.  Note: 3DEP provides server side interpolatin given best available data",
)
@click.option("-v", "--verbose", default=False, type=bool, help="verbose ouput")
@pass_nldi_xstool
def xsatendpts(
    nldi_xstool: "NLDIXSTool",
    startpt: Tuple[float, float],
    endpt: Tuple[float, float],
    crs: str,
    numpoints: int,
    resolution: str,
    file: Any,
    verbose: bool,
) -> int:
    """bla.

    Parameters
    ----------
    nldi_xstool : NLDIXSTool
        [description]
    startpt : Tuple[float, float]
        [description]
    endpt : Tuple[float, float]
        [description]
    crs : str
        [description]
    numpoints : int
        [description]
    resolution : str
        [description]
    file : Any
        [description]
    verbose : bool
        [description]

    Returns
    -------
    [type]
        [description]
    """
    x1 = startpt[0]
    y1 = startpt[1]
    x2 = endpt[0]
    y2 = endpt[1]
    nl = "\n"
    if verbose:
        print(
            f"input:  {nl}, \
            start: {startpt}, {nl}, \
            end: {endpt}, {nl}, \
            x1:{x1}, y1:{y1}, {nl}, \
            x2:{x2}, y2:{y2}, {nl}, \
            npts={numpoints}, {nl}, \
            resolution={resolution}, \
            input_crs={crs}, {nl}, \
            output_crs={nldi_xstool.outcrs()}  {nl}, \
            file={file}, {nl}, \
            verbose: {verbose} "
        )
    path = []
    path.append(startpt)
    path.append(endpt)
    # print(type(path))
    xs = getxsatendpts(
        path=path, numpts=numpoints, res=resdict.get(resolution), crs=crs, file=file
    )
    if file is None:
        print(xs.to_json())
    return 0


if __name__ == "__main__":
    sys.exit(main(prog_name="nldi-xstool"))  # pragma: no cover
