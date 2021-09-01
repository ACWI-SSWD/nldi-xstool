"""Tools for extending USGS measured Bathymetry (preliminary)."""
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from geopandas.array import points_from_xy
from shapely.geometry import Point

from nldi_xstool.nldi_xstool import getxsatendpts


class ExtADCPBathy:
    """Class to facilitate extending USGS measured bathymetry cross-sections."""

    def __init__(
        self: "ExtADCPBathy",
        file: str,
        dist: float,
        lonstr: str,
        latstr: str,
        estr: str,
        acrs: str,
    ) -> None:
        """Init ExtADCPBathy class.

        Parameters
        ----------
        self : ExtADCPBathy
            [description]
        file : str
            [description]
        dist : float
            [description]
        lonstr : str
            [description]
        latstr : str
            [description]
        estr : str
            [description]
        acrs : str
            [description]
        """
        self.afile = Path(file)
        assert self.afile.exists()
        self.adata = pd.read_csv(self.afile)
        self.agdf2 = gpd.GeoDataFrame(
            self.adata, geometry=points_from_xy(self.adata[lonstr], self.adata[latstr])
        )
        self.crs = acrs
        self.agdf = self.agdf2.set_crs(acrs)
        self.agdf["elevation"] = self.adata[estr]

        # convert to albers conic for geometry calculations
        self.agdf = self.agdf.to_crs("epsg:5071")

        # clean up dataframe by deleting old names
        del self.agdf[lonstr]
        del self.agdf[latstr]
        del self.agdf[estr]

        self.ext = dist
        self.xs_complete = gpd.GeoDataFrame()

        self._buildgeom()

    def _distance(self: "ExtADCPBathy", p1t: Point, p2t: Point) -> np.float64:
        """Convenience function to calc distance between 2 points."""
        return np.float64(np.sqrt(np.sum(np.square(np.array(p2t) - np.array(p1t)))))

    def _buildgeom(self: "ExtADCPBathy") -> None:
        npts = len(self.agdf)
        p1 = np.array(self.agdf.geometry[0])
        p2 = np.array(self.agdf.geometry[npts - 1])
        dx = p2[0] - p1[0]
        dy = p2[1] - p1[1]
        theta = np.arctan2(dy, dx)
        length = np.sqrt(np.sum(np.square(p2 - p1)))
        p2ny = p1[1] + (length + self.ext + 1) * np.sin(theta)
        p2nx = p1[0] + (length + self.ext + 1) * np.cos(theta)
        p1ny = p1[1] - (self.ext + 1) * np.sin(theta)
        p1nx = p1[0] - (self.ext + 1) * np.cos(theta)

        df_pre = pd.DataFrame(
            [{"lon": p1nx, "lat": p1ny}, {"lon": p1[0], "lat": p1[1]}]
        )

        df_post = pd.DataFrame(
            [{"lon": p2[0], "lat": p2[1]}, {"lon": p2nx, "lat": p2ny}]
        )

        gdf_pre = gpd.GeoDataFrame(
            df_pre, geometry=gpd.points_from_xy(df_pre.lon, df_pre.lat)
        ).set_crs("epsg:5071")
        # del gdf_pre['distance']
        gdf_pre_geo = gdf_pre.to_crs("epsg:4326")

        gdf_post = gpd.GeoDataFrame(
            df_pre, geometry=gpd.points_from_xy(df_post.lon, df_post.lat)
        ).set_crs("epsg:5071")
        # del gdf_post['distance']
        gdf_post_geo = gdf_post.to_crs("epsg:4326")

        new_df_pre = self._getxs(gdf_pre_geo, int(self.ext), 1).to_crs("epsg:5071")
        new_df_post = self._getxs(gdf_post_geo, int(self.ext), 1).to_crs("epsg:5071")
        del new_df_pre["distance"]
        del new_df_post["distance"]
        new_df_pre["code"] = "0"
        new_df_post["code"] = "0"
        self.agdf["code"] = "1"

        self.xs_complete = gpd.GeoDataFrame(
            pd.concat([new_df_pre, self.agdf, new_df_post], ignore_index=True),
            crs="epsg:5071",
        )

        self.xs_complete["station"] = 0.0
        for index, v in self.xs_complete.iterrows():
            if index == 0:
                p1 = v.geometry
            self.xs_complete.at[index, "station"] = self._distance(p1, v.geometry)

    def _getxs(
        self: "ExtADCPBathy", gdf: gpd.GeoDataFrame, numpts: int, res: int
    ) -> gpd.GeoDataFrame:
        """Convenience wrapper for nldi-xstool.getxsatendpts.

        Parameters
        ----------
        self : ExtADCPBathy
            [description]
        gdf : gpd.GeoDataFrame
            [description]
        numpts : int
            [description]
        res : int
            [description]

        Returns
        -------
        gpd.GeoDataFrame
            [description]
        """
        return getxsatendpts(
            [
                (gdf.geometry[0].x, gdf.geometry[0].y),
                (gdf.geometry[1].x, gdf.geometry[1].y),
            ],
            numpts=numpts,
            crs="epsg:4326",
            res=res,
        )

    def get_xs_complete(self: "ExtADCPBathy") -> gpd.GeoDataFrame:
        """Return extened cross-section.

        Parameters
        ----------
        self : ExtADCPBathy
            [description]

        Returns
        -------
        [type]
            [description]
        """
        return self.xs_complete.to_crs(self.crs)
