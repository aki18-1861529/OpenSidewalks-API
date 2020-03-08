import geopandas as gpd
from shapely import geometry
from shapely.ops import snap

curbs = gpd.read_file('CurbRamp/CurbRamp.shp')
crossings = gpd.read_file('Crossings/Crossings.shp')

# filter undefined crossings out of data
crossings = crossings[crossings['MARKING_TY'] != '2']


def connect_curbs_crossings(curbs, crossings, simplify=0.05):
    curbs.geometry = curbs.geometry.simplify(simplify)
    curbs.geometry = curbs.geometry.buffer(5.0, cap_style=1)    # add buffers
    curbs = curbs.to_crs(crossings.crs)     # make projections

    # snap curbs to crossing that are within distance
    # loops through curbs and crossings to determine the distance between them
    # note: very slow due to for loops
    result = list()
    for i in curbs.geometry:
        crossing_filtered = crossings[crossings['geometry'].distance(i) <= 0.5]
        for j in crossing_filtered['geometry']:
            result.append(snap(j, i, 0.5))


def main():
    connect_curbs_crossings(curbs, crossings)

if __name__ == "__main__":
    main()
