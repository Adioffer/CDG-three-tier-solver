"""
Example usage:
    map = MapBuilder('test')
    map.add_frontends()
    map.add_point(target, 'estimated-location-of-server-04')
    map.save_map()
"""

import folium
import os

from CDGeB1.data_classes import ProbeClient, DataCenter


class MapBuilder:
    def __init__(self, map_name='', probe_clients: ProbeClient = None, datacenters: DataCenter = None):
        self.map = folium.Map(location=(0, 0), zoom_start=2)
        self.map_name = f'map_{map_name}.html'
        self.probe_clients = probe_clients
        self.datacenters = datacenters

    def add_probes(self):
        # Display all probes
        if self.probe_clients:
            for probe in self.probe_clients:
                probe_name, coordinates = probe.name, probe.coordinates
                # Note: some probes have same location as frontend servers, and folium fails to display them both.
                # Therefore, a slight delta is added. (157 km)
                new_coords = (coordinates[0] + 1, coordinates[1] + 1)
                folium.Marker(location=new_coords,
                              popup=f'{probe_name}: {str(coordinates)}',
                              tooltip=probe_name,
                              icon=folium.Icon(color='darkgreen', icon='satellite-dish', prefix='fa')
                              ).add_to(self.map)

    def add_datacenter(self):
        # Display all frontends
        if self.datacenters:
            for datacenter in self.datacenters:
                datacenter_name, location = datacenter.name, datacenter.coordinates
                folium.Marker(location=location[:2],
                              popup=f'{datacenter_name}: {str(location[:2])}',
                              tooltip=datacenter_name,
                              icon=folium.Icon(color='blue', icon='server', prefix='fa')
                              ).add_to(self.map)

    def add_point(self, coordinates, label='', color='red'):
        folium.Marker(location=coordinates,
                      popup=str(coordinates),
                      tooltip=label,
                      icon=folium.Icon(color=color)
                      ).add_to(self.map)

    def add_circle(self, center, radius):
        folium.Circle(location=center, radius=1000 * radius, color='blue', fill=True, fill_color='blue',
                      fill_opacity=0.03).add_to(self.map)

    def add_dashed_line(self, start, end, color='blue'):
        folium.PolyLine([start, end], color=color, dash_array='10, 10').add_to(self.map)

    def add_line(self, start, end, color='green'):
        folium.PolyLine([start, end], color=color).add_to(self.map)

    def save_map(self, path):
        self.map.save(os.path.join(path, self.map_name))


def make_map_with_all_frontends():
    map = MapBuilder('all_frontends')
    map.add_probes()
    map.add_datacenter()
    map.save_map()

# make_map_with_all_frontends()
