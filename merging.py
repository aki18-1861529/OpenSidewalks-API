import geopandas as gp
import numpy as np
from shapely import geometry
import networkx as nx
import pyproj as proj
import numexpr as num
import json 
import pickle
from workspace import street_name_exists

#bellevue data pickle: bellevue0526
#aus data pickle: sgraphs_aus_bounded.pickle
with open('bellevue0603.pickle', 'rb') as f:
    sgraphs_data = pickle.load(f)

def merge_edges(G):
    starting_nodes = []
    newG = nx.DiGraph()
    # make a list of starting nodes 
    # print("SUBGRAPH EDGES \n")
    # print(G.edges(data=True))
    for n in G.nodes():
        if G.degree(nbunch=n) == 2: # in-degree plus out-degree
            starting_nodes.append(n)
        if G.degree(nbunch=n) == 0:
            G.remove_node(n)




    print("starting nodes count: ", len(starting_nodes))  
    # iterate through starting nodes to connect sidewalks
    for node in starting_nodes:
        geom_all = []
        first_neigh = next(G.successors(node))
        edge_data_1 = G.get_edge_data(node, first_neigh)
        # print(edge_data_1)
        init_geom = edge_data_1['geometry']
        fwd = edge_data_1['forward']
        street = edge_data_1['street']
        geom_all.append(init_geom)
        print("starting node ", node)
        print("first neigh ", first_neigh)
        prev_neigh = node
        while G.degree(nbunch=first_neigh) != 2: #in-degree plus out-degree. caught in loop here?
            second_neigh = G.successors(first_neigh)  # Returns an iterator over successor nodes of n.
            for neigh in second_neigh:
                if neigh != prev_neigh and neigh != first_neigh: # select node going in correct direction
                    second_neigh = neigh 
            edge_data_2 = G.get_edge_data(first_neigh, second_neigh)
            next_geom = edge_data_2['geometry']
            geom_all.append(next_geom)
            prev_neigh = first_neigh
            first_neigh = second_neigh
        dict_info = {
            'forward': fwd,
            'street': street,
            'geometry': geom_all,
        }
        newG.add_edge(node, first_neigh, **dict_info)
    return newG



def main():
    # print(len(sgraphs))
    combined = nx.DiGraph() # giant graph - combination of all subgraphs
    for sg in sgraphs_data:
        if street_name_exists:
            sg = merge_edges(sg)
        sg_edges = sg.edges(data=True)
        combined.add_edges_from(sg_edges)

    
    # Output as edgelist
    # nx.write_edgelist(combined,'bell_data_edges.edgelist')
    
    # Output as GeoJSON
    allFeatures = list()
    for e in combined.edges(data=True):
        # get starting node and ending node
        startn = e[0]
        point1 = []
        point2 = []
        edge_geom = []
        endn = e[1]
        # add starting node to coordinates array
        point1.append(startn[0])
        point1.append(startn[1])
        edge_geom.append(point1)
        
        # get dictionary of data with rest of geom
        ddict = e[2].get("geometry")

        # get forward, street, and visited information
        fwd = e[2].get("forward")
        street = e[2].get("street")
        surface = e[2].get("surface").lower()

        #add next point
        if not isinstance(ddict, list):
            ddict = [ddict]
        nextSeg = ddict[0]
        nextPoint = nextSeg.coords[0]
        point2.append(nextPoint[0])
        point2.append(nextPoint[1])
        edge_geom.append(point2)

        

        # iterate through linestrings, create and add array of segment with arrays of points
        for linestring in ddict:
            segCoords = linestring.coords
            for point in segCoords:
                newPoint = []
                newPoint.append(point[0])
                newPoint.append(point[1])
                edge_geom.append(newPoint)

        # add second to last point
        ptFinal1 = []
        lastSeg = ddict[len(ddict)-1]
        lastPoint = lastSeg.coords[-1]
        ptFinal1.append(lastPoint[0])
        ptFinal1.append(lastPoint[1])

        # add final point
        ptFinal2 = []
        ptFinal2.append(endn[0])
        ptFinal2.append(endn[1])

        # add last segment of edge
        edge_geom.append(ptFinal1)
        edge_geom.append(ptFinal2)

        info = {"highway": "footway", "surface": surface}
        gmt = {"type": "LineString", "coordinates": edge_geom}

        feat = {"type": "Feature", "geometry": gmt, "properties": info}

        allFeatures.append(feat)

    featCollection = {"type": "FeatureCollection", "features": allFeatures}

    
    with open('bell_edges_603_v2.json', 'w') as f:  # writing JSON object
        json.dump(featCollection, f)


     


if __name__ == "__main__":
    main()
