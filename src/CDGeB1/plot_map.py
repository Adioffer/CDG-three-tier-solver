"""
Example usage:
    map = MapBuilder('test')
    map.add_frontends()
    map.add_point(target, 'estimated-location-of-server-04')
    map.save_map()
"""

import folium
from common import probe_locations, frontend_locations


class MapBuilder:
    def __init__(self, map_name=''):
        self.map = folium.Map(location=(0, 0), zoom_start=2)
        self.map_name = f'out\\map_{map_name}.html'

    def add_probes(self):
        # Display all probes
        for probe_name, coordinates in probe_locations.items():
            # Note: some probes have same location as frontend servers, and folium fails to display them both.
            # Therefore, a slight delta is added. (157 km)
            new_coords = (coordinates[0] + 1, coordinates[1] + 1)
            folium.Marker(location=new_coords, 
                            popup=f'{probe_name}: {str(coordinates)}', 
                            tooltip=probe_name,
                            icon=folium.Icon(color='darkgreen', icon='satellite-dish', prefix='fa')
                            ).add_to(self.map)

    def add_frontends(self):
        # Display all frontends
        for frontend_name, coordinates in frontend_locations.items():
            folium.Marker(location=coordinates, 
                            popup=f'{frontend_name}: {str(coordinates)}', 
                            tooltip=frontend_name,
                            icon=folium.Icon(color='blue', icon='server', prefix='fa')
                            ).add_to(self.map)

    def add_point(self, coordinates, label='', color='red'):
        folium.Marker(location=coordinates, 
                      popup=str(coordinates), 
                      tooltip=label,
                      icon=folium.Icon(color=color)
                    ).add_to(self.map)
    
    def add_circle(self, center, radius):
        folium.Circle(location=center, radius=1000*radius, color='blue', fill=True, fill_color='blue',
                    fill_opacity=0.03).add_to(self.map)

    def save_map(self):
        self.map.save(self.map_name)


def make_map_with_all_frontends():
    map = MapBuilder('all_frontends')
    map.add_probes()
    map.add_frontends()
    map.save_map()

# make_map_with_all_frontends()
