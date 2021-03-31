package com.kellieblog.geojson.main;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

import java.io.*;
import java.util.*;

public class Main {
    static class Node {
        int id;
        double x;
        double y;
        boolean isEndPoint = false;
    }

    private static Map<Integer, HashMap<Integer, String>> edgesMap;
    private static Map<Integer, Node> nodeSet;
    private static Map<Integer, Integer> pointsToConnectMap;
    public static final double DEFAULT_DISTANCE = 25.0d;

    public static void main(String[] args) throws IOException {
        System.out.println("Init...");
        init();

        System.out.println("Checking the end points...");
        checkEndPoints();

        System.out.println("Connecting the points...");
        checkPointsNeedConnect();

        System.out.println("Generating the result...");
        generateResult();

        System.out.println("Result generated (output_edges.geojson)");
    }

    private static void generateResult() throws IOException {
        BufferedWriter bufferedWriter = new BufferedWriter(new FileWriter(new File("output_edges.geojson")));
        BufferedReader bufferedReader = new BufferedReader(new FileReader(new File("edges.geojson")));
        String line;
        while (!(line = bufferedReader.readLine()).equals("]")) {
            line = line.replace("\"street\": \"null\", ", "");
            bufferedWriter.write(line.replace("Asphalt","asphalt")
                    .replace("Concrete","concrete")
                    .replace("Gravel","gravel")
                    .replace("Grass","grass")
                    .replace("Paved","paved")
                    .replace("Paving_stones","paving_stones")
                    .replace("Unpaved","unpaved")+ "\n");

        }
        bufferedReader.close();
        bufferedWriter.write(",\n");
        int mapSize = pointsToConnectMap.size();
        int counter = 1;
        for (Integer nodeId : pointsToConnectMap.keySet()) {
            bufferedWriter.write("{ \"type\": \"Feature\", \"properties\": { \"forward\": 1," +
                    "\"surface\": \"concrete\", \"node_start\": " + nodeId + ", \"node_end\": " + pointsToConnectMap.get(nodeId) + " }," +
                    " \"geometry\": { \"type\": \"LineString\", \"coordinates\": [ [ " + nodeSet.get(nodeId).x + ", " + nodeSet.get(nodeId).y + "]" +
                    ",[" + nodeSet.get(pointsToConnectMap.get(nodeId)).x + ", " + nodeSet.get(pointsToConnectMap.get(nodeId)).y + "] ] } }");
            if (counter++ < mapSize) {
                bufferedWriter.write(",\n");
            } else {
                bufferedWriter.write("\n");
            }
        }

        bufferedWriter.write("]}\n");
        bufferedWriter.close();
    }

    private static void checkPointsNeedConnect() {
        pointsToConnectMap = new HashMap<>();
        for (Integer node : nodeSet.keySet()) {
            if (nodeSet.get(node).isEndPoint) {
                for (Integer node1 : nodeSet.keySet()) {
                    if (nodeSet.get(node).id != nodeSet.get(node1).id && nodeSet.get(node1).isEndPoint && twoPointsDistance(nodeSet.get(node), nodeSet.get(node1)) < DEFAULT_DISTANCE) {
                        pointsToConnectMap.put(nodeSet.get(node).id, nodeSet.get(node1).id);
                    }
                }
            }
        }
    }

    private static double twoPointsDistance(Node node1, Node node2) {
        return Math.sqrt(Math.pow(node1.x - node2.x, 2) + Math.pow(node1.y - node2.y, 2));
    }

    public static void checkEndPoints() {
        Map<Integer, HashSet<Integer>> relationMap = new TreeMap<>();
        for (Integer nodeId : edgesMap.keySet()) {
            if (!relationMap.containsKey(nodeId)) {
                relationMap.put(nodeId, new HashSet<>());
            }
            for (Integer secondNodeId : edgesMap.get(nodeId).keySet()) {
                relationMap.get(nodeId).add(secondNodeId);
                if (!relationMap.containsKey(secondNodeId)) {
                    relationMap.put(secondNodeId, new HashSet<>());
                }
                relationMap.get(secondNodeId).add(nodeId);
            }

        }

        for (Integer node : nodeSet.keySet()) {
            if (relationMap.get(nodeSet.get(node).id).size() == 1) {
                nodeSet.get(node).isEndPoint = true;
            }
        }
    }

    public static void init() {
        JsonObject jsonObject = convertFileToJSON("edges.geojson");
        edgesMap = new HashMap<>();
        JsonArray jsonElements = jsonObject.get("features").getAsJsonArray();
        for (int i = 0; i < jsonElements.size(); i++) {
            JsonObject object = jsonElements.get(i).getAsJsonObject();
            JsonObject properties = object.getAsJsonObject("properties");
            if (!edgesMap.containsKey(properties.get("node_start").getAsInt())) {
                edgesMap.put(properties.get("node_start").getAsInt(), new HashMap<>());
            }
            edgesMap.get(properties.get("node_start").getAsInt()).put(properties.get("node_end").getAsInt(), object.toString());
        }

        JsonObject nodesJsonObject = convertFileToJSON("nodes.geojson");

        nodeSet = new LinkedHashMap<>();
        JsonArray jsonElements1 = nodesJsonObject.get("features").getAsJsonArray();
        for (int i = 0; i < jsonElements1.size(); i++) {
            Node node = new Node();
            JsonObject object = jsonElements1.get(i).getAsJsonObject();
            JsonObject properties = object.getAsJsonObject("properties");
            JsonArray coord = object.getAsJsonObject("geometry").getAsJsonArray("coordinates");
            node.id = properties.get("nodeID").getAsInt();
            node.x = coord.get(0).getAsDouble();
            node.y = coord.get(1).getAsDouble();
            nodeSet.put(node.id, node);
        }
    }

    public static JsonObject convertFileToJSON(String fileName) {

        JsonObject jsonObject = new JsonObject();
        try {
            JsonParser parser = new JsonParser();
            JsonElement jsonElement = parser.parse(new FileReader(fileName));
            jsonObject = jsonElement.getAsJsonObject();
        } catch (FileNotFoundException e) {
            e.printStackTrace();
        }
        return jsonObject;
    }

}
