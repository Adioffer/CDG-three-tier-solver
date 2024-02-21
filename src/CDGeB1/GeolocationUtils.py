import numpy as np
from common import Continent


class GeolocationUtils():
    """
    This class is used before geolocation a target.
    It contains some useful methods.
    """
    @classmethod
    def haversine(cls, coord1, coord2):
        """
        Computes Haversine distance between two given coordinates.
        """
        lat1, lon1 = np.radians(coord1)
        lat2, lon2 = np.radians(coord2)
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        distance = 6371.0 * c  # Radius of Earth in kilometers

        return distance
    
    @classmethod
    def pretty_print_rates(cls, rates):
        """
        Uses Rich to pretty-print the rates between each continent.

        @param rates: Output of evaluate_csp_rates.
        """
        from rich.console import Console
        from rich.table import Table

        # Extract unique row headers and column headers
        rows = sorted(set(str(key[0]) for key in rates))
        columns = sorted(set(str(key[1]) for key in rates))

        # Create a Rich table
        table = Table(title="Data Table")

        # Add the columns to the table, first column for row headers
        table.add_column("", justify="right", style="cyan", no_wrap=True)
        for column in columns:
            table.add_column(column, justify="center")

        # Add rows and their corresponding data to the table
        for row in rows:
            row_data = [str(rates.get((row, column), "")) for column in columns]
            table.add_row(row, *row_data)

        # Print the table
        console = Console()
        console.print(table)
    
    def __init__(self,
                 true_file_frontend_mapping,
                 probe_locations, 
                 frontend_locations,
                 frontend_continents,
                 file_locations,
                 # Optionals:
                 closets_probe_to_frontends = None,
                 closest_file_for_frontend = None,
                 csp_delays = None,
                 csp_distances = None
                 ):
        self.true_file_frontend_mapping = true_file_frontend_mapping
        self.probe_locations = probe_locations
        self.frontend_locations = frontend_locations
        self.frontend_continents = frontend_continents
        self.file_locations = file_locations
        self.closets_probe_to_frontends = closets_probe_to_frontends
        self.closest_file_for_frontend = closest_file_for_frontend
        self.csp_delays = csp_delays
        self.csp_distances = csp_distances

    def build_distance_map(self):
        distances = dict()
        for frontend, frontend_location in self.frontend_locations.items():
            for filename, file_location in self.file_locations.items():
                distances[(frontend, filename)] = self.haversine(frontend_location, file_location)
        return distances

    def determine_closest_probes(self):
        """
        Determine the closest probe to each front-end server.
        """
        closest_probes = dict()
        for frontend in self.frontend_locations:
            closest_probes[frontend] = min(self.probe_locations, key=lambda probe: self.haversine(self.frontend_locations[frontend], self.probe_locations[probe]))

        return closest_probes

    def determine_closest_files(self, measurements_to_all_targets):
        """
        Determine the file to be located within the same DC as each front-end server.
        Assuming they have the least rtt between them. 
        """
        closest_file_for_frontend = dict()
        for frontend in self.frontend_locations:
            closest_file_measurement = min(measurements_to_all_targets.items(),
                # pair = (key=(probe_name,frontend_name,filename), value=min_rtt)
                key=lambda pair: pair[1] if \
                    # front-end == frontent
                    pair[0][1] == frontend and \
                    # probe = closest to frontend
                    pair[0][0] == self.closets_probe_to_frontends[frontend]
                    else float('inf'))
            closest_file_for_frontend[frontend] = closest_file_measurement[0][2]
        
        return closest_file_for_frontend

    def compute_csp_delays(self, measurements_to_all_targets):
        """
        Compute the round-trip times of the second hop (front-end to file)
        """
        rtts_within_csp = dict()
        for frontend in self.frontend_locations:
            closest_file = self.closest_file_for_frontend[frontend]
            closest_probe = self.closets_probe_to_frontends[frontend]
            
            for filename in self.file_locations:
                rtts_within_csp[(frontend, filename)] = \
                    measurements_to_all_targets[(closest_probe, frontend, filename)] - \
                    measurements_to_all_targets[(closest_probe, frontend, closest_file)]
        
        return rtts_within_csp

    def _evaluate_rates_inner(self, continent_a=None, continent_b=None):
        """ Evaluate the communication rates within CSP network.
        Given every frontent->file delay and distance.
        If continents are not specified - all continents will be considered.
        
        return: rate [km/s]
        """

        Xs, Ys = list(), list()
        for frontend in self.frontend_locations:
            for filename in self.file_locations:
                # Filter the relevant measurements
                if continent_a and continent_b:
                    if continent_a != self.frontend_continents[frontend] or \
                      continent_b != self.frontend_continents[self.true_file_frontend_mapping[filename]]:
                        continue

                distance = self.csp_distances[(frontend, filename)]
                delay = self.csp_delays[(frontend, filename)]
                
                Xs.append(distance)
                Ys.append(delay)

        slope = np.linalg.lstsq(np.array(Xs)[:, np.newaxis], np.array(Ys), rcond=None)[0][0]

        return round(1 / slope, 2)

    def evaluate_csp_general_rate(self):
        """
        Computes the general transmission rate within the CSP's network.
        """
        general_rate = self._evaluate_rates_inner()
        return general_rate
        
    def evaluate_csp_rates(self):
        """
        Computes the transmission rates within the CSP's network, considering the continents.
        """
        rates = dict()
        for continent_a in Continent:
            for continent_b in Continent:
                rate = self._evaluate_rates_inner(continent_a, continent_b)
                rates[(continent_a, continent_b)] = rate
        
        return rates