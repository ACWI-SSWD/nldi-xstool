"""Generate cross-section using NLDI and user-defined point."""
from typing import Tuple

import geopandas as gpd
import numpy as np
import numpy.typing as npt
import pandas as pd
from shapely.geometry import LineString
from shapely.geometry import Point

from .centerline import Centerline


class XSGen:
    """XSGEN class.

    The XSGen class generates a cross-section on a stream segment given a location,
    width number of points. It fits a tension spline to stream segment, and
    calculated cross-section perpendicular from sline.
    """

    def __init__(
        self: "XSGen",
        point: gpd.GeoDataFrame,
        cl_geom: gpd.GeoDataFrame,
        ny: int,
        width: float,
        tension: float = 10.0,
    ) -> None:
        """Build cross-section using NLDI based on a point near a stream-segment to NHD.

        Args:
            point (gpd.GeoDataFrame): [description]
            cl_geom (gpd.GeoDataFrame): [description]
            ny (int): [description]
            width (float): [description]
            tension (float, optional): [description]. Defaults to 10.0.  # noqa DAR103
        """
        self.cl_geom = cl_geom
        self.point = point
        self.tension = tension
        self.width = width
        self.cl_length = self.cl_geom.geometry[0].length
        self.cl_npts = len(self.cl_geom.geometry[0].coords)
        if self.cl_length < 10.0:
            self.nx = 10
        else:
            self.nx = int(self.cl_length / 3)
        if self.nx % 2 == 0:
            self.nx += 1
        if ny % 2 == 0:
            ny += 1
        self.ny = ny
        # if self.cl_length > 20.0:
        #     self.nx = int(self.cl_length / 10)
        # else:
        #     self.nx = int(self.cl_length / 1)
        self.cl = Centerline(cl_geom, self.nx, self.tension)
        self.x = np.zeros(self.ny, dtype=np.double)
        self.y = np.zeros(self.ny, dtype=np.double)
        self._buildxs()

    def _get_perp_index(
        self: "XSGen", clx: npt.NDArray[np.double], cly: npt.NDArray[np.double]
    ) -> int:
        mind = 1e6
        id = -1
        for index, p in enumerate(zip(clx, cly)):
            dist = np.sqrt(
                np.power(self.point.geometry[0].x - p[0], 2)
                + np.power(self.point.geometry[0].y - p[1], 2)
            )
            if dist < mind:
                mind = dist
                id = index

        return id

    def _buildxs(self: "XSGen") -> None:
        clx, cly = self.cl.getinterppts()
        delt = np.double(self.width / (self.ny - 1))
        nm = int((self.ny + 1) / 2)
        index = self._get_perp_index(clx, cly)

        for id, j in enumerate(range(0, self.ny)):
            self.x[id] = clx[index] + delt * (nm - j - 1) * np.sin(
                self.cl.getphiinterp(index)
            )
            self.y[id] = cly[index] - delt * (nm - j - 1) * np.cos(
                self.cl.getphiinterp(index)
            )

    def get_xs(self: "XSGen") -> gpd.GeoDataFrame:
        """Get Geopandas DataFrame of generated cross-section.

        Returns:
            Geopandas DataFrame: Of generated cross-section
        """
        points = gpd.GeoSeries(map(Point, zip(self.x, self.y)))
        ls = LineString((points.to_list()))
        d = {0: {"name": "cross-section", "geometry": ls}}
        df = pd.DataFrame.from_dict(d, orient="index")
        gdf = gpd.GeoDataFrame(df, geometry=df.geometry, crs=self.point.crs)
        return gdf

    def get_xs_points(
        self: "XSGen",
    ) -> Tuple[npt.NDArray[np.double], npt.NDArray[np.double]]:
        """Get cross-section points.

        Returns:
            numpy array: Arrays of x and y points of cross-section.
        """
        return self.x, self.y

    def get_strm_seg_spline(self: "XSGen") -> gpd.GeoDataFrame:
        """Get the resulting splined stream-segment.

        Returns:
            Geopandas DataFrame: Of splined stream-segment.
        """
        x, y = self.cl.getinterppts()
        points = gpd.GeoSeries(map(Point, zip(x, y)))
        ls = LineString((points.to_list()))
        d = {0: {"name": "strm_seg_spline", "geometry": ls}}
        df = pd.DataFrame.from_dict(d, orient="index")
        gdf = gpd.GeoDataFrame(df, geometry=df.geometry)
        return gdf
