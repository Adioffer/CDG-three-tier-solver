import numpy as np
from scipy.optimize import minimize
import folium

def haversine_distance(coord1, coord2):
    R = 6371.0
    lat1, lon1 = np.radians(coord1)
    lat2, lon2 = np.radians(coord2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    distance = R * c
    return distance
def objective_function(pos, dist, probes):
    distances = np.array([haversine_distance(pos, probe) for probe in probes])
    return np.sum((distances - dist) ** 2)
def triangulate(probe_positions, distances):
    print(len(probe_positions))
    print(len(distances))
    print(probe_positions)
    print()
    print(distances)
    exit(0)
    initial_guess = np.mean(probe_positions, axis=0)
    result = minimize(objective_function, initial_guess, args=(distances, probe_positions), method='L-BFGS-B', options={'disp': True})
    return result.x

node_positions = {
    "cdgeb-server-01": (39.0469, -77.4903),
    "cdgeb-server-02": (51.5088, -0.093),
    "cdgeb-server-03": (-23.5335, -46.6359),
    "cdgeb-server-04": None,
    "cdgeb-server-05": (1.2929, 103.8547),
    "cdgeb-server-06": (45.5075, -73.5887),
    "cdgeb-server-07": (39.9587, -82.9987),
    "cdgeb-server-08": (37.1835, -121.7714),
    "cdgeb-server-09": (45.8234, -119.7257),
    "cdgeb-server-10": (19.0748, 72.8856),
    "cdgeb-server-11": (34.6946, 135.5021),
    "cdgeb-server-12": (37.4585, 126.7015),
    "cdgeb-server-13": (-33.8715, 151.2006),
    "cdgeb-server-14": (50.1188, 8.6843),
    "cdgeb-server-15": (53.3379, -6.2591),
    "cdgeb-server-16": (48.4323, 2.4075),
    "cdgeb-server-17": (59.3287, 18.0717),
}

distances_from_cdgeb_server_04 = [10870.07, 9556.81, 18531.6, 0, 5317.24, 10387.62, 10536.01, 8354.46, 7969.29, 6722.83, 396.24, 1175.37, 7826.4, 9330.62, 9585.19, 9748.68]
probe_positions = np.array([node_positions[node] for node in node_positions if node != "cdgeb-server-04"])
distances = np.array(distances_from_cdgeb_server_04)
estimated_cdgeb_server_04 = triangulate(probe_positions, distances)
node_positions["cdgeb-server-04"] = tuple(estimated_cdgeb_server_04)
print("Estimated Location of cdgeb-server-04:", node_positions["cdgeb-server-04"])



m = folium.Map(location=(0, 0), zoom_start=2)
for node, coord in node_positions.items():
    if coord is not None:
        folium.Marker(location=coord, popup=node).add_to(m)
for node, coord in node_positions.items():
    if coord is not None and node != "cdgeb-server-04":
        if node in node_positions.keys() and node in distances_from_cdgeb_server_04:
            circle_radius = distances_from_cdgeb_server_04[node_positions.keys().index(node)] * 1000
            folium.Circle(location=coord, radius=circle_radius, color='blue', fill=True, fill_color='blue',
                          fill_opacity=0.03).add_to(m)
true_intersection = np.array([35.6893, 139.6899])
print(haversine_distance((35.6893, 139.6899),estimated_cdgeb_server_04))
folium.Marker(location=true_intersection, popup='True Intersection',
              icon=folium.Icon(color='green')).add_to(m)
folium.Marker(location=estimated_cdgeb_server_04, popup='Estimated Intersection',
              icon=folium.Icon(color='red')).add_to(m)
map_filename = 'map_cdgeb_server_04.html'
m.save(map_filename)
print(f"Map saved as {map_filename}")
