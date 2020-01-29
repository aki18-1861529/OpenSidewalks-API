import geopandas as gp
import numpy as np
from shapely import geometry
import networkx as nx

sdw = gp.read_file('Sidewalks/geo_export_8f5a3f72-4a94-4006-84e5-650856822b59.shp')


sdw_exists = sdw[sdw["pedestrian"] != 'ABSENT_SIDEWALKS']


def create_graph(gdf, precision=1, simplify=0.05):
    # The geometries sometimes have tiny end parts - get rid of those!
    gdf.geometry = gdf.geometry.simplify(simplify)
    gdf = gdf.groupby('full_stree')

 


    # undirected graph for each of them. 
    # connected subgraphs 
    # know which node to start on - degree of 1
    # exceptions: degree > 2 incorrect
    # pass through coordinates and connect them

    #directional vs non directional graphs



# print(res.head())



# print(result.geom_type)

#convert linestring geometry object to array of coordinates

# the geometry column


# geom = sdw.geometry

# def join_lines(coords, precision):

