"""Class for generateing a cross-section from a path of points.

Currently only 2 points can make up a path as in a cross-section.
"""
from typing import Tuple

import geopandas as gpd
import numpy as np
import numpy.typing as npt
import pandas as pd
from shapely.geometry import LineString
from shapely.geometry import Point


class PathGen:
    """Pathgen class."""

    def __init__(self: "PathGen", path_geom: gpd.GeoDataFrame, ny: int) -> None:
        """Init PathGen.

        Args:
            path_geom (gpd.GeoDataFrame): [description]
            ny (int): [description]
        """
        # print(path_geom, ny)
        self.path_geom = path_geom
        self.width = self.path_geom.geometry[0].length
        if ny % 2 == 0:
            ny += 1
        self.ny = ny
        self.x = np.zeros(self.ny, dtype=np.double)
        self.y = np.zeros(self.ny, dtype=np.double)
        self.int_path = None
        self.__buildpath()

    def __buildpath(self: "PathGen") -> None:
        line = self.path_geom.geometry[0]
        spacing = line.length / self.ny
        # print(line, spacing)
        d = 0.0
        index = 0
        while d < self.width and index < self.ny:
            point = line.interpolate(d)
            self.x[index] = point.x
            self.y[index] = point.y
            d += spacing
            index += 1

    def get_xs(self: "PathGen") -> gpd.GeoDataFrame:
        """Get resulting cross-section.

        Returns:
            Geopandas Dataframe: Return a Geopandas DataFrame of resulting cross-section
        """
        points = gpd.GeoSeries(map(Point, zip(self.x, self.y)))
        ls = LineString((points.to_list()))
        # print(ls)
        d = {0: {"name": "section-path", "geometry": ls}}
        df = pd.DataFrame.from_dict(d, orient="index")
        gdf = gpd.GeoDataFrame(df, geometry=df.geometry, crs=self.path_geom.crs)
        return gdf

    def get_xs_points(
        self: "PathGen",
    ) -> Tuple[npt.NDArray[np.double], npt.NDArray[np.double]]:
        """Get cross-sectin points.

        Returns:
            numpy arrays: Returns Numpy arrays of x and y points in cross-section.
        """
        return self.x, self.y
