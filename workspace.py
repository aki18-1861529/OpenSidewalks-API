import geopandas as gp
import numpy as np
from shapely import geometry
import networkx as nx
import pyproj as proj
import numexpr as num 
import pickle
import sys


bbox = (-97.74655,30.28317,-97.73650,30.26129)
# Austin Data: ('Sidewalks/geo_export_8f5a3f72-4a94-4006-84e5-650856822b59.shp')
# Bellevue Data: '/home/kellie/Desktop/pythonworkspace/OpenSidewalks-API/PedestrianFacilities_COBApr2020.shp'
# sdw = gp.read_file('/home/kellie/Desktop/pythonworkspace/OpenSidewalks-API/PedestrianFacilities_COBApr2020.shp')

sdw = gp.read_file(sys.argv[1])

# fill blank values
sdw['Material'] = sdw['Material'].fillna("Null")

if "pedestrian" in sdw.keys():
    sdw_exists = sdw[sdw["pedestrian"] != 'ABSENT_SIDEWALKS']
else:
    sdw_exists = sdw

# cast coordinates to projected system (meters)
sdw_exists = sdw_exists.to_crs("EPSG:4326")


# check if street name is provided in dataset
street_name_exists = False
if "full_stree" in sdw_exists.keys():
    street_name_exists = True



def create_graph(gdf, precision=1, simplify=0.05):

    # The geometries sometimes have tiny end parts - get rid of those!
    gdf.geometry = gdf.geometry.simplify(simplify)

    

    # Set street name 
    if street_name_exists:
        street_name = gdf.iloc[0,3]
    else:
        street_name = "null"

    G = nx.DiGraph()


    # round coords
    def make_node(coord, precision):
        return tuple(np.round(coord, precision))
     
    # helper function to create edges
    def add_edges_sub(G, precision, coords, street_name, material):
        geom = geometry.LineString(coords[::])
        geom_r = geometry.LineString(coords[::-1])
        start = make_node(coords[0], precision) # first element
        end = make_node(coords[-1], precision) # last element


        # edge case - to avoid nodes with more than 4 degrees
        if G.degree(nbunch=start) == 4:
            start = make_node(coords[0], 3)
        if G.degree(nbunch=end) == 4:
            end = make_node(coords[-1], 3)


        # Add forward edge
        fwd_attr = {
            'forward': 1,
            'geometry': geom,
            'street': street_name,
            'surface': material,
        }
        G.add_edge(start, end, **fwd_attr)

        # Add reverse edge
        rev_attr = {
            'forward': 0,
            'geometry': geom_r,
            'street': street_name,
            'surface': material,
        }
        G.add_edge(end, start, **rev_attr)

 
    # Edges are stored as (from, to, data), where from and to are nodes.
    def add_edges(row, G, precision=precision):
        
        geom = row.geometry
        material = row['Material']

        # adjust material values to OSM standard
        if material == "Boardwalk":
            material = "wood"
        elif material == "Brick":
            material = "paving_stones"

        
        if geom.geom_type == "MultiLineString" and street_name_exists:
            multicoords = [list(line.coords) for line in geom] #gets coordinates of all linestrings
            # Making a flat list -> LineString
            simple = geometry.LineString([item for sublist in multicoords for item in sublist])
            coords = list(simple.coords)
        elif geom.geom_type == "MultiLineString" and not street_name_exists:
            for line in geom: #gets coordinates of all linestrings
                coords = list(line.coords)
                add_edges_sub(G, precision, coords, street_name, material)
        elif geom.geom_type == "LineString":
            coords = geom.coords
            add_edges_sub(G, precision, coords, street_name, material)
            


    gdf.apply(add_edges, axis=1, args=[G])

    return G






def graph_workflow(gdf, precision=1):
    grouped = gdf.groupby(["full_stree"], as_index=False)
    # undirected subgraphs for each street name
    subgraphs = []

    def create_subgraph(group):
        G = create_graph(group)
        subgraphs.append(G)

    grouped.apply(create_subgraph)

    return subgraphs






def main():
    if street_name_exists:
        sgraphs = graph_workflow(sdw_exists)
    else:
        sgraphs = []
        sgraphs.append(create_graph(sdw_exists, street_name_exists))
    
    with open('bellevue0603.pickle', 'wb') as f:
    # Pickle the 'data' dictionary using the highest protocol available.
        pickle.dump(sgraphs, f, pickle.HIGHEST_PROTOCOL)

    

    # for combining: seattle repo. mid-block crosswalk. where crossings get joined to sidewalks


if __name__ == "__main__":
    main()




        
