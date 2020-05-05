import geopandas as gp
import numpy as np
from shapely import geometry
import networkx as nx
import pyproj as proj
import numexpr as num


sdw = gp.read_file('Sidewalks/geo_export_8f5a3f72-4a94-4006-84e5-650856822b59.shp')


sdw_exists = sdw[sdw["pedestrian"] != 'ABSENT_SIDEWALKS']

def create_graph(gdf, precision=1, simplify=0.05):
    # The geometries sometimes have tiny end parts - get rid of those!
    gdf.geometry = gdf.geometry.simplify(simplify)
    G = nx.DiGraph()


    # round coords
    def make_node(coord, precision):
        return tuple(np.round(coord, precision))
     
    
 
    # Edges are stored as (from, to, data), where from and to are nodes.
    # az1 is the azimuth of the first segment of the geometry (point into the
    # geometry), az2 is for the last segment (pointing out of the geometry)
    def add_edges(row, G, precision=precision):
        # setup your projections
        # crs_wgs = proj.Proj(init='epsg:4326') # WGS84 geographic
        # crs_bng = proj.Proj(init='epsg:102005')

        
        geom = row.geometry
                

        if geom.geom_type == "MultiLineString":
            multicoords = [list(line.coords) for line in geom]
            # Making a flat list -> LineString
            simple = geometry.LineString([item for sublist in multicoords for item in sublist])
            coords = list(simple.coords)
        elif geom.geom_type == "LineString":
            coords = geom.coords

        # cast coordinates to projected system
        # for c in coords:
            # c = proj.transform(crs_wgs, crs_bng, c[0], c[1])

        geom = geometry.LineString(coords[::])
        geom_r = geometry.LineString(coords[::-1])
        start = make_node(coords[0], precision) # first element
        end = make_node(coords[-1], precision) # last element

        # Add forward edge
        fwd_attr = {
            'forward': 1,
            'geometry': geom,
            # 'az1': azimuth(coords[0], coords[1]),
            # 'az2': azimuth(coords[-2], coords[-1]),
            'visited': 0,
        }
        G.add_edge(start, end, **fwd_attr)

        # Add reverse edge
        rev_attr = {
            'forward': 0,
            'geometry': geom_r,
            # 'az1': azimuth(coords_r[0], coords_r[1]),
            #'az2': azimuth(coords_r[-2], coords_r[-1]),
            'visited': 0,
        }
        G.add_edge(end, start, **rev_attr)



    gdf.apply(add_edges, axis=1, args=[G])

    return G

    # undirected graph for each of them. 
    # connected subgraphs: 
    # know which node to start on - degree of 1
    # exceptions: degree > 2 incorrect
    # pass through coordinates and connect them

    #directional vs non directional graphs








def graph_workflow(gdf, precision=1):
    grouped = gdf.groupby("full_stree")
    # undirected subgraphs for each street name
    subgraphs = []

    def create_subgraph(group):
        G = create_graph(group)
        subgraphs.append(G)

    grouped.apply(create_subgraph)

    return subgraphs





def merge_edges(G):
    starting_nodes = []
    newG = nx.DiGraph()
    # make a list of starting nodes 
    for n in G.nodes(G):
        if G.degree(nbunch=n) == 2: # in-degree plus out-degree
            starting_nodes.append(n)
    # iterate through starting nodes to connect sidewalks
    for node in starting_nodes:
        geom_all = []
        first_neigh = G.successors(node)
        edge_data_1 = G.get_edge_data(node, first_neigh)
        init_geom = edge_data_1[node][first_neigh]['geometry']
        fwd = init_geom = edge_data_1[node][first_neigh]['forward']
        geom_all.append(init_geom)
        while G.degree(G, nbunch=first_neigh) != 2: #in-degree plus out-degree
            second_neigh = G.successors(first_neigh)  # Returns an iterator over successor nodes of n.
            for neigh in second_neigh:
                if neigh is not first_neigh: # select node going in correct direction
                    second_neigh = neigh 
            edge_data_2 = G.get_edge_data(first_neigh, second_neigh)
            next_geom = edge_data_2[first_neigh][second_neigh]['geometry']
            geom_all.append(next_geom)
            first_neigh = second_neigh
        dict_info = {
            'forward': fwd,
            'geometry': geom_all,
        }
        newG.add_edge(node, first_neigh, dict_info)
    return newG


def main():
    sgraphs = graph_workflow(sdw_exists)
    for sg in sgraphs:
       sg = merge_edges(sg)
    # combined = nx.disjoint_union_all(sgraphs)
    # new_gdf = nx.to_pandas_adjacency(combined)
    # new_gdf.to_file("sdw_connect_test.shp")
    print("complete!")


if __name__ == "__main__":
    main()




        
