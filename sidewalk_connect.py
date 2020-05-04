import pandas as pd
import numpy as np
import geopandas as gpd
# from shapely.ops import snap, nearest_points

curbs = gpd.read_file('CurbRamp/CurbRamp.shp')
crossings = gpd.read_file('Crossings/Crossings.shp')

# filter undefined crossings out of data
crossings = crossings[crossings['MARKING_TY'] != '2']
crossings = crossings[['geometry', 'GlobalID', 'SHAPE_Leng', 'SDE_GLOBAL']]
curbs = curbs[['geometry', 'GlobalID']]


def connect_curbs_crossings(curbs, crossings, simplify=0.05):
    curbs.geometry = curbs.geometry.simplify(simplify)
    curbs = curbs.to_crs(crossings.crs)     # make projections
    curbs.to_csv('curbs.csv')

    crossings.sindex
    offset = 100
    bbox = curbs.bounds + [-offset, -offset, offset, offset]
    hits = bbox.apply(lambda row: list(crossings.sindex.intersection(row)),
                      axis=1)     # get list of crossings that overlap
    temp = pd.DataFrame({"pt_index": np.repeat(hits.index, hits.apply(len)),
                        "line_i": np.concatenate(hits.values)})
    temp = temp.join(crossings.reset_index(drop=True), on="line_i")
    temp = temp.join(curbs.geometry.rename("point"), on="pt_index")
    temp = gpd.GeoDataFrame(temp, geometry="geometry", crs=curbs.crs)
    # calculate distance between curb point and crossing line
    temp["snap_dist"] = temp.geometry.distance(gpd.GeoSeries(temp.point))
    temp = temp.loc[temp.snap_dist <= 100]
    temp = temp.sort_values(by=["snap_dist"])
    temp.to_csv('temp.csv')
    closest = temp.groupby("pt_index").first()
    closest = gpd.GeoDataFrame(closest, geometry="geometry")
    pos = closest.geometry.project(gpd.GeoSeries(closest.point))
    new_pts = closest.geometry.interpolate(pos)
    line_columns = ["geometry"]
    snapped = gpd.GeoDataFrame(closest[line_columns], geometry=new_pts)
    updated_points = curbs.drop(columns=["geometry"]).join(snapped)
    updated_points = updated_points.dropna(subset=["geometry"])

    updated_points.to_csv('updated_points.csv')
    print(snapped.head())
    print(updated_points.head())
    print(curbs["geometry"].head())


def main():
    connect_curbs_crossings(curbs, crossings)


if __name__ == "__main__":
    main()
