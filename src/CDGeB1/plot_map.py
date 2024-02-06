"""
Example usage:
    map = MapBuilder('test')
    map.add_frontends()
    map.add_point(target, 'estimated-location-of-server-04')
    map.save_map()
"""

import folium
from common import frontend_locations


class MapBuilder:
    def __init__(self, map_name=''):
        self.map = folium.Map(location=(0, 0), zoom_start=2)
        self.map_name = f'out\\map_{map_name}.html'

    def add_frontends(self):
        # Display all frontends
        for frontend_name, coordinates in frontend_locations.items():
            if coordinates is not None:
                folium.Marker(location=coordinates, popup=f'{frontend_name}: {str(coordinates)}', tooltip=frontend_name).add_to(self.map)

    def add_point(self, coordinates, label='', color='red'):
        folium.Marker(location=coordinates, popup=str(coordinates), tooltip=label,
                    icon=folium.Icon(color=color)).add_to(self.map)
    
    def add_circle(self, center, radius):
        folium.Circle(location=center, radius=1000*radius, color='blue', fill=True, fill_color='blue',
                    fill_opacity=0.03).add_to(self.map)

    def save_map(self):
        self.map.save(self.map_name)


# for backup:
def _display_map(estimated_coordinate, real_coordinate=None, map_name=''):
    # Init map
    map = folium.Map(location=(0, 0), zoom_start=2)

    # Display all frontends
    for node, coord in frontend_locations.items():
        if coord is not None:
            folium.Marker(location=coord, popup=node).add_to(map)

    # Display circles
    # for node, coord in frontend_locations.items():
    #     if coord is not None and node != "cdgeb-server-04":
    #         if node in frontend_locations.keys() and node in distances_from_cdgeb_server_04:
    #             circle_radius = distances_from_cdgeb_server_04[frontend_locations.keys().index(node)] * 1000
    #             folium.Circle(location=coord, radius=circle_radius, color='blue', fill=True, fill_color='blue',
    #                         fill_opacity=0.03).add_to(map)
                    
    # Display estimated location
    folium.Marker(location=estimated_coordinate, popup='Estimated Intersection',
                icon=folium.Icon(color='red')).add_to(map)
    
    # Display real location
    if real_coordinate:
        folium.Marker(location=real_coordinate, popup='True Intersection',
                    icon=folium.Icon(color='green')).add_to(map)
    
    map_filename = f'out\\map_{map_name}.html'
    map.save(map_filename)
