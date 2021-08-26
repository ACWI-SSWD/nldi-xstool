"""Created on Tue May  5 16:26:25 2015.

@author: mweier
"""
# -*- coding: utf-8 -*-
import numpy as np
from numba import jit

# noqa N803


@jit
def channelbuilder(wsdepth, rightss, leftss, widthbottom):
    """.

    Builds trapziodal channel station/elevation array given depth,
    right side slope, left side slope, and bottom width
    """
    lefttoe = wsdepth * 1.25 * leftss
    righttoe = wsdepth * 1.25 * rightss
    staelev = np.array(
        [
            (0.0, wsdepth * 1.25),
            (lefttoe, 0.0),
            (lefttoe + widthbottom, 0.0),
            (lefttoe + widthbottom + righttoe, wsdepth * 1.25),
        ]
    )
    return staelev


def lineintersection(line1, line2):
    """lineintersection.

    Args:
        line1 ([type]): [description]
        line2 ([type]): [description]

    Returns:
        [type]: [description]
    """
    xdiff = (line1[0][0] - line1[1][0], line2[0][0] - line2[1][0])
    ydiff = (line1[0][1] - line1[1][1], line2[0][1] - line2[1][1])

    def det(a, b):
        return a[0] * b[1] - a[1] * b[0]

    div = det(xdiff, ydiff)
    if div == 0:
        x = y = np.nan
        #        print 'lines do not intersect'
        return x, y

    d = (det(*line1), det(*line2))
    x = det(d, xdiff) / div
    y = det(d, ydiff) / div
    return x, y


@jit
def polygon_area(corners):
    """polygon_area.

    Args:
        corners ([type]): [description]

    Returns:
        [type]: [description]
    """
    area = 0.0
    for i in range(len(corners)):
        j = (i + 1) % len(corners)
        area += corners[i][0] * corners[j][1]
        area -= corners[j][0] * corners[i][1]
    area = abs(area) / 2.0
    return area


@jit
def channel_perimeter(corners):  # noqa N806
    p = 0.0
    for i in range(len(corners) - 1):
        p += np.sqrt(
            (
                np.power((corners[i + 1][0] - corners[i][0]), 2)
                + np.power((corners[i + 1][1] - corners[i][1]), 2)
            )
        )
    return p


def flow_est(wselev, n, slope, staelev, units):  # noqa N806
    """[summary].

    Estimates uniform flow using the Manning equation for
    a user defined trapziodal channel or a manually defined channel using
    a station/elevation file

    Args:
        wselev ([type]): [description]
        n ([type]): [description]
        slope ([type]): [description]
        staelev ([type]): [description]
        units ([type]): [description]

    Returns:
        [type]: [description]
    """
    if units == "m":
        const = 1.0
    else:
        const = 1.49

    intersectlist = []
    for i in range(0, len(staelev)):
        x, y = lineintersection(
            (staelev[i - 1], staelev[i]),
            ([staelev[0][0], wselev], [staelev[-1][0], wselev]),
        )
        if x >= staelev[i - 1][0] and x <= staelev[i][0] and abs(y - wselev) < 0.01:
            #             print (x,y)
            intersectlist.append((x, y))
        else:
            #             print ('line segments do not intersect')
            pass

    try:
        intersectarray = np.array(intersectlist)
        intersectarray = intersectarray[intersectarray[:, 0].argsort()]
        # print 'more than two points intersect'
        staminelev = staelev[np.where(staelev[:, 1] == min(staelev[:, 1]))][0][0]
        startpoint = intersectarray[np.where(intersectarray[:, 0] < staminelev)][-1]
        endpoint = intersectarray[np.where(intersectarray[:, 0] > staminelev)][0]
        intersectarray = np.vstack([startpoint, endpoint])
    except Exception as e:
        print(e)
        return 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0

    stamin = np.min(intersectarray[:, 0])
    stamax = np.max(intersectarray[:, 0])

    thalweig = staelev[np.where(staelev[:, 1] == np.min(staelev[:, 1]))]

    minelev = thalweig[:, 1][0]
    maxdepth = wselev - minelev

    if len(intersectarray) < 2:
        return 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0

    staelevtrim = np.vstack([intersectarray[0], staelev, intersectarray[1]])
    # staelevtrim = staelevtrim[staelevtrim[:,0].argsort()]
    staelevtrim = staelevtrim[
        np.where((staelevtrim[:, 0] >= stamin) & (staelevtrim[:, 0] <= stamax))
    ]

    area = polygon_area(staelevtrim)
    r = area / channel_perimeter(staelevtrim)
    v = (const / n) * np.power(r, (2.0 / 3.0)) * np.sqrt(slope)
    q = v * area
    topwidth = stamax - stamin
    xground = staelev[:, 0]
    yground = staelev[:, 1]
    yground0 = np.ones(len(xground)) * np.min(yground)
    xwater = staelevtrim[:, 0]
    ywater = np.ones(len(xwater)) * wselev
    ywater0 = staelevtrim[:, 1]
    args = (
        r,
        area,
        topwidth,
        q,
        v,
        maxdepth,
        xground,
        yground,
        yground0,
        xwater,
        ywater,
        ywater0,
    )
    return args
