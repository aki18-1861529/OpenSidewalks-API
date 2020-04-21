import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.ops import snap

curbs = gpd.read_file('CurbRamp/CurbRamp.shp')
crossings = gpd.read_file('Crossings/Crossings.shp')

# filter undefined crossings out of data
crossings = crossings[crossings['MARKING_TY'] != '2']
crossings = crossings[['geometry', 'GlobalID', 'SHAPE_Leng', 'SDE_GLOBAL']]
curbs = curbs[['geometry', 'GlobalID']]


def connect_curbs_crossings(curbs, crossings, simplify=0.05):
    curbs.geometry = curbs.geometry.simplify(simplify)
    curbs.geometry = curbs.geometry.buffer(5.0, cap_style=1)    # add buffers
    curbs = curbs.to_crs(crossings.crs)     # make projections

    # source: https://medium.com/@brendan_ward/how-to-leverage-geopandas-for-faster-snapping-of-points-to-lines-6113c94e59aa
    crossings.sindex
    offset = 100
    bbox = curbs.bounds + [-offset, -offset, offset, offset]
    hits = bbox.apply(lambda row: crossings(crossings.sindex.intersection(row)), axis=1)

    tmp = pd.DataFrame({"pt_idx": np.repeat(hits.index, hits.apply(len)), "line_i": np.concatenate(hits.values)})
    tmp = tmp.join(crossings.reset_index(drop=True), on="line_i")
    tmp = tmp.join(curbs.geometry.rename("point"), on="pt_idx")
    tmp = gpd.GeoDataFrame(tmp, geometry="geometry", crs=curbs.crs)
    tmp["snap_dist"] = tmp.geometry.distance(gpd.GeoSeries(tmp.point))
    tmp = tmp.loc[tmp.snap_dist <= 0.5]
    tmp = tmp.sort_values(by=["snap_dist"])
    
    closest = tmp.groupby("pt_idx").first()
    closest = gpd.GeoDataFrame(closest, geometry="geometry")

    pos = closest.geometry.project(gpd.GeoSeries(closest.point))
    new_pts = closest.geometry.interpolate(pos)
    line_columns = ['GlobalID']
    snapped = gpd.GeoDataFrame(closest[line_columns],geometry=new_pts)
    updated_points = curbs.drop(columns=["geometry"]).join(snapped)
    updated_points = updated_points.dropna(subset=["geometry"])

    # previous:
    # # snap curbs to crossing that are within distance
    # # loops through curbs and crossings to determine the distance between them
    # # note: very slow due to for loops
    # result = list()
    # for i in curbs.geometry:
    #     crossing_filtered = crossings[crossings['geometry'].distance(i) <= 0.5]
    #     for j in crossing_filtered['geometry']:
    #         result.append(snap(j, i, 0.5))

    # print(result)


def main():
    connect_curbs_crossings(curbs, crossings)


if __name__ == "__main__":
    main()
