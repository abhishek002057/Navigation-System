"""
hospital_graph.py
------------------
This module represents the HOSPITAL BUILDING as a weighted GRAPH.

- Each NODE = a location inside the hospital (Entrance, Reception,
  Cardiology, Orthopedic, etc.)
- Each EDGE = a corridor/path connecting two locations, with a WEIGHT
  representing the distance (in meters) or walking time.

We use DIJKSTRA'S ALGORITHM to find the SHORTEST PATH from the
Entrance to whichever department the AI model predicts.

This is a pure Python implementation using a min-heap (priority queue)
so it runs efficiently even on larger hospital maps.
"""

import heapq

# --------------------------------------------------------------------
# STEP 1: Define the Hospital Map as a Graph (Adjacency List)
# --------------------------------------------------------------------
# Format: { "Node": {"NeighborNode": distance_in_meters, ...}, ... }
#
# You can freely edit this dictionary to match YOUR real hospital's
# floor plan. Just add nodes and connect them with realistic distances.

HOSPITAL_GRAPH = {
    "Entrance": {"Reception": 10, "Parking": 5},
    "Parking": {"Entrance": 5},
    "Reception": {"Entrance": 10, "Corridor A": 8, "Corridor B": 12, "Pharmacy": 6},
    "Pharmacy": {"Reception": 6},
    "Corridor A": {"Reception": 8, "Cardiology": 15, "Neurology": 20, "Orthopedic": 18},
    "Corridor B": {"Reception": 12, "Dermatology": 10, "ENT": 14, "Ophthalmology": 16,
                   "General Medicine": 9},
    "Cardiology": {"Corridor A": 15},
    "Neurology": {"Corridor A": 20, "Psychiatry": 10},
    "Orthopedic": {"Corridor A": 18, "Corridor C": 12},
    "Corridor C": {"Orthopedic": 12, "Gastroenterology": 14, "Urology": 16, "Pediatrics": 20},
    "Dermatology": {"Corridor B": 10},
    "ENT": {"Corridor B": 14},
    "Ophthalmology": {"Corridor B": 16},
    "General Medicine": {"Corridor B": 9},
    "Psychiatry": {"Neurology": 10},
    "Gastroenterology": {"Corridor C": 14},
    "Urology": {"Corridor C": 16},
    "Pediatrics": {"Corridor C": 20},
}


def dijkstra_shortest_path(graph, start, end):
    """
    Finds the shortest path between `start` and `end` nodes using
    Dijkstra's Algorithm.

    Returns:
        path (list): ordered list of nodes from start to end
        distance (int/float): total distance of the shortest path
    """
    # distances[node] = shortest known distance from start to node
    distances = {node: float("inf") for node in graph}
    distances[start] = 0

    # previous[node] = the node we came from (used to rebuild the path)
    previous = {node: None for node in graph}

    # Min-heap priority queue: (distance, node)
    priority_queue = [(0, start)]
    visited = set()

    while priority_queue:
        current_distance, current_node = heapq.heappop(priority_queue)

        if current_node in visited:
            continue
        visited.add(current_node)

        # Stop early once we reach the destination
        if current_node == end:
            break

        # Check all neighbors of the current node
        for neighbor, weight in graph.get(current_node, {}).items():
            distance = current_distance + weight
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                previous[neighbor] = current_node
                heapq.heappush(priority_queue, (distance, neighbor))

    # If the end node was never reached, there is no valid path
    if distances[end] == float("inf"):
        return None, None

    # Rebuild the path by walking backwards from `end` to `start`
    path = []
    node = end
    while node is not None:
        path.append(node)
        node = previous[node]
    path.reverse()

    return path, distances[end]


def get_shortest_path_to_department(department, start="Entrance"):
    """
    Convenience wrapper used by the Flask app.
    Given a predicted department name, returns the shortest path
    from the hospital Entrance to that department.
    """
    if department not in HOSPITAL_GRAPH:
        return {
            "error": f"Department '{department}' not found in hospital map."
        }

    path, distance = dijkstra_shortest_path(HOSPITAL_GRAPH, start, department)

    if path is None:
        return {"error": f"No path found from {start} to {department}."}

    return {
        "path": path,
        "distance_meters": distance
    }


# ----------------------------------------------------------------------
# Quick manual test when running this file directly:
#   python graph/hospital_graph.py
# ----------------------------------------------------------------------
if __name__ == "__main__":
    result = get_shortest_path_to_department("Cardiology")
    print("Shortest path to Cardiology:")
    print(result)
