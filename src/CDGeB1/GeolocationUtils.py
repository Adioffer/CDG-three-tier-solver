import numpy as np
from CDGeB1.common import Continent
import warnings

warnings.filterwarnings("ignore", "divide by zero encountered in scalar divide", category=RuntimeWarning)


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
        table = Table(title="Transmission Rates (km/s) within CSP Network")

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
                 file_frontend_mapping,
                 probe_locations,
                 frontend_locations,
                 frontend_continents,
                 file_locations,
                 datacenter_locations,
                 # Optionals:
                 closets_probe_to_frontends=None,
                 closest_file_for_frontend=None,
                 csp_delays=None,
                 csp_distances=None
                 ):
        self.file_frontend_mapping = file_frontend_mapping
        self.probe_locations = probe_locations
        self.frontend_locations = frontend_locations
        self.frontend_continents = frontend_continents
        self.file_locations = file_locations
        self.closets_probe_to_frontends = closets_probe_to_frontends
        self.closest_file_for_frontend = closest_file_for_frontend
        self.csp_delays = csp_delays
        self.csp_distances = csp_distances
        self.datacenter_locations = datacenter_locations

    def build_distance_map(self):
        distances = dict()
        for frontend, frontend_location in self.frontend_locations.items():
            for filename, file_location in self.file_locations.items():
                distances[(frontend, filename)] = self.haversine(frontend_location[:2], file_location[:2])
        return distances

    def determine_closest_probes(self):
        """
        Determine the closest probe to each front-end server.
        """
        closest_probes = dict()
        for frontend in self.frontend_locations:
            closest_probes[frontend] = min(self.probe_locations,
                                           key=lambda probe: self.haversine(self.frontend_locations[frontend][:2],
                                                                            self.probe_locations[probe][:2]))

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

        # pretty print closest_file_for_frontend, in each row:
        print("Closest file for each front-end server: \n",
              '\n'.join([f'{k}:\t{v}' for k, v in closest_file_for_frontend.items()]))

        return closest_file_for_frontend

    def compute_csp_delays_intra_dc_poc(self, measurements_to_all_targets):
        intra_dc = {"cdgeb-server-01": 0.013363,
                    "cdgeb-server-02": 0.011441,
                    "cdgeb-server-03": 0.018753,
                    "cdgeb-server-04": 0.019172,
                    "cdgeb-server-05": 0.012989,
                    "cdgeb-server-06": 0.011617,
                    "cdgeb-server-07": 0.012338,
                    "cdgeb-server-08": 0.012499,
                    "cdgeb-server-09": 0.014998,
                    "cdgeb-server-10": 0.01144,
                    "cdgeb-server-11": 0.011053,
                    "cdgeb-server-12": 0.012879,
                    "cdgeb-server-13": 0.013707,
                    "cdgeb-server-14": 0.012099,
                    "cdgeb-server-15": 0.013234,
                    "cdgeb-server-16": 0.011779,
                    "cdgeb-server-17": 0.013305,
                    }

        rtts_within_csp = dict()
        for frontend in self.frontend_locations:
            closest_file = self.closest_file_for_frontend[frontend]
            closest_probe = self.closets_probe_to_frontends[frontend]

            for filename in self.file_locations:
                rtts_within_csp[(frontend, filename)] = \
                    measurements_to_all_targets[(closest_probe, frontend, filename)] - \
                    measurements_to_all_targets[(closest_probe, frontend, closest_file)] \
                    + intra_dc[frontend]

                if rtts_within_csp[(frontend, filename)] < 0:
                    print("ERROR: Negative RTT!")
                    # rtts_within_csp[(frontend, filename)] = 0 # Avoid negative values

                if measurements_to_all_targets[(closest_probe, frontend, filename)] - \
                        measurements_to_all_targets[(closest_probe, frontend, closest_file)] < 0:
                    print("ERROR: Negative RTT for RTT2-RTT1!")

        return rtts_within_csp

    def compute_csp_delays(self, measurements_to_all_targets):
        """
        Compute the round-trip times of the second hop (front-end to file)
        """

        # self.compute_csp_delays_intra_dc_poc(measurements_to_all_targets)

        rtts_within_csp = dict()
        for frontend in self.frontend_locations:
            closest_file = self.closest_file_for_frontend[frontend]
            closest_probe = self.closets_probe_to_frontends[frontend]

            for filename in self.file_locations:
                rtts_within_csp[(frontend, filename)] = \
                    measurements_to_all_targets[(closest_probe, frontend, filename)] - \
                    measurements_to_all_targets[(closest_probe, frontend, closest_file)]

        return rtts_within_csp

    def compute_csp_delays_test(self, measurements_1party, measurements_3party, frontend_3party, filenames):
        rtts_within_csp = dict()
        for frontend_3party in frontend_3party:
            closest_file_in_1party = self.closest_file_for_frontend[frontend_3party]
            closest_probe_in_1party = self.closets_probe_to_frontends[frontend_3party]

            for filename in filenames:
                rtts_within_csp[(frontend_3party, filename)] = \
                    measurements_3party[(closest_probe_in_1party, frontend_3party, filename)] - \
                    measurements_1party[(closest_probe_in_1party, frontend_3party, closest_file_in_1party)]

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
                            continent_b != self.datacenter_locations[self.file_frontend_mapping[filename]][2]:
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
