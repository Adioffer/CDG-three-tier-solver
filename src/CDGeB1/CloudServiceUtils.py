import numpy as np
from CDGeB1.data_classes import *
import warnings
from scipy.optimize import minimize
from numpy import square

warnings.filterwarnings("ignore", "divide by zero encountered in scalar divide", category=RuntimeWarning)

__all__ = ["haversine", "pretty_print_rates", "DatasetUtils1Party", "DatasetUtils3Party"]

MEASUREMENT_PROBES = 0
MEASUREMENT_FRONTENDS = 1
MEASUREMENT_FILES = 2


def haversine(coord1: tuple[float, float], coord2: tuple[float, float]) -> float:
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


def pretty_print_rates(rates: dict[tuple[Continent, Continent], float]):
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


class DatasetUtils:
    def __init__(self,
                 # Common:
                 measurements: dict[tuple[str, str, str], float],
                 datacenters: list[DataCenter],
                 probe_clients: list[ProbeClient],
                 frontend_servers: list[FrontEnd],
                 data_files: list[DataFile],
                 # 3-party:
                 possible_file_datacenters: list[DataCenter] = None,  # required for 3-party
                 solutions: dict[DataFile, DataCenter] = None,
                 # 1-party:
                 closest_probe_to_frontend: dict[FrontEnd, ProbeClient] = None,
                 closest_file_for_frontend: dict[FrontEnd, DataFile] = None,
                 # Optionals:
                 csp_distances: dict[tuple[FrontEnd, DataFile], float] = None,
                 csp_delays: dict[tuple[FrontEnd, DataFile], float] = None,
                 csp_rates: dict[tuple[Continent, Continent], float] = None,
                 ):
        # Common:
        self.measurements = measurements
        self.datacenters = datacenters
        self.probe_clients = probe_clients
        self.frontend_servers = frontend_servers
        self.data_files = data_files
        # 3-party:
        self.possible_file_datacenters = possible_file_datacenters
        self.solutions = solutions
        # 1-party:
        self.closest_probe_to_frontend = closest_probe_to_frontend
        self.closest_file_for_frontend = closest_file_for_frontend
        # Optionals:
        self.csp_distances = csp_distances
        self.csp_delays = csp_delays
        self.csp_rates = csp_rates

        self.determine_closest_probes()

    @property
    def datacenter_locations(self):
        return [datacenter.coordinates for datacenter in self.datacenters]

    @property
    def probe_locations(self):
        return [probe.coordinates for probe in self.probe_clients]

    @property
    def frontend_locations(self):
        return [frontend.coordinates for frontend in self.frontend_servers]

    @property
    def file_locations(self):
        return [datafile.coordinates for datafile in self.data_files]

    @property
    def datacenter_continents(self):
        return [datacenter.continent for datacenter in self.datacenters]

    @property
    def probe_continents(self):
        return [probe.continent for probe in self.probe_clients]

    @property
    def frontend_continents(self):
        return [frontend.datacenter.continent for frontend in self.frontend_servers]

    @property
    def file_continents(self):
        return [datafile.datacenter.continent for datafile in self.data_files]

    @property
    def datacenter_names(self):
        return [datacenter.name for datacenter in self.datacenters]

    @property
    def probe_names(self):
        return [probe.name for probe in self.probe_clients]

    @property
    def frontend_names(self):
        return [frontend.name for frontend in self.frontend_servers]

    @property
    def file_names(self):
        return [datafile.name for datafile in self.data_files]

    def determine_closest_probes(self):
        """
        Determine the closest probe to each front-end server.
        """
        closest_probes = dict()
        for frontend in self.frontend_servers:
            closest_probes[frontend] = min(self.probe_clients,
                                           key=lambda probe: haversine(frontend.coordinates,
                                                                       probe.coordinates))

        self.closest_probe_to_frontend = closest_probes
        return closest_probes

    def determine_closest_files(self):
        """
        Determine the file to be located within the same DC as each front-end server.
        Assuming they have the least rtt between them.
        """
        print("[DEBUG] determine_closest_files using the complex method.")
        print("NOT YET IMPLEMENTED")  # TODO refactor according to the new data structures
        exit(1)
        # closest_file_for_frontend = dict()
        # for frontend in self.frontend_servers:
        #     closest_file_measurement = min(self.measurements.items(),
        #                                    # pair = (key=(probe_name,frontend_name,filename), value=min_rtt)
        #                                    key=lambda pair: pair[1] if \
        #                                    # front-end == frontend
        #                                    pair[0][1] == frontend and \
        #                                    # probe = closest to frontend
        #                                    pair[0][0] == self.closets_probe_to_frontend[frontend]
        #                                    else float('inf'))
        #     closest_file_for_frontend[frontend] = closest_file_measurement[0][2]
        #
        # # pretty print closest_file_for_frontend, in each row:
        # print("Closest file for each front-end server: \n",
        #       '\n'.join([f'{k}:\t{v}' for k, v in closest_file_for_frontend.items()]))
        #
        # return closest_file_for_frontend

    def compute_csp_delays_optimizer(self):
        mode_closest_probes_only = True

        frontend_names = self.frontend_names
        num_frontends = len(frontend_names)
        file_names = self.file_names
        num_files = len(file_names)

        if mode_closest_probes_only:
            probe_names = [probe.name for probe in self.closest_probe_to_frontend.values()]
            num_probes = len(probe_names)

            closest_probe_to_frontend_names = {frontend.name: probe.name for frontend, probe in
                                               self.closest_probe_to_frontend.items()}
            measurements = {k: v for k, v in self.measurements.items()
                            if k[MEASUREMENT_PROBES] == closest_probe_to_frontend_names[k[MEASUREMENT_FRONTENDS]]}
        else:
            probe_names = self.probe_names
            num_probes = len(probe_names)

            measurements = self.measurements

        # Initial guess for the delays
        count_rtts_1hop = num_probes * num_frontends
        count_rtts_2hop = num_frontends * num_files
        initial_guess = np.zeros(count_rtts_1hop + count_rtts_2hop)
        param_bounds = (
                [(0, None)] * len(initial_guess)
        )

        def loss_function(x):
            probe_server_delays = x[:count_rtts_1hop].reshape((num_probes, num_frontends))
            server_file_delays = x[count_rtts_1hop:].reshape((num_frontends, num_files))

            total_loss = 0
            for (probe_name, frontend_name, file_name), measured_rtt in measurements.items():
                probe_index = probe_names.index(probe_name)
                frontend_index = frontend_names.index(frontend_name)
                file_index = file_names.index(file_name)

                estimated_rtt = probe_server_delays[probe_index, frontend_index] + server_file_delays[
                    frontend_index, file_index]
                total_loss += square(measured_rtt - estimated_rtt)
            return total_loss

        result = minimize(loss_function, initial_guess, method='L-BFGS-B', bounds=param_bounds)

        optimized_params = result.x
        rtts_1hop = optimized_params[:count_rtts_1hop].reshape((num_probes, num_frontends))
        rtts_2hop = optimized_params[count_rtts_1hop:].reshape((num_frontends, num_files))

        rtts_within_csp = {
            (frontend, data_file): rtts_2hop[frontend_names.index(frontend.name), file_names.index(data_file.name)]
            for frontend in self.frontend_servers
            for data_file in self.data_files}

        self.csp_delays = {k: (v / 2) for k, v in rtts_within_csp.items()}
        return self.csp_delays


class DatasetUtils1Party(DatasetUtils):
    """
    This class represents the DatasetUtils for the 1-party service.
    """

    # Don't override the __init__ method, as it is the same as the parent class.
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.build_distance_map()

        self.closest_file_for_frontend = {frontend: min(self.data_files,
                                                        key=lambda data_file: haversine(frontend.coordinates,
                                                                                        data_file.coordinates))
                                          for frontend in self.frontend_servers}

    def build_distance_map(self):
        distances = dict()
        for frontend in self.frontend_servers:
            for data_file in self.data_files:
                distances[(frontend, data_file)] = haversine(frontend.coordinates,
                                                             data_file.coordinates)

        self.csp_distances = distances
        return self.csp_distances

    def compute_csp_delays_subtraction(self):
        """
        Compute the round-trip times of the second hop (front-end to file)
        Using the subtraction method.
        """

        rtts_within_csp = dict()
        for frontend in self.frontend_servers:
            closest_file = self.closest_file_for_frontend[frontend]
            closest_probe = self.closest_probe_to_frontend[frontend]

            for data_file in self.data_files:
                rtts_within_csp[(frontend, data_file)] = \
                    self.measurements[(closest_probe.name, frontend.name, data_file.name)] - \
                    self.measurements[(closest_probe.name, frontend.name, closest_file.name)]

        self.csp_delays = {k: (v / 2) for k, v in rtts_within_csp.items()}
        return self.csp_delays

    def _evaluate_rates_inner(self, continent_a=None, continent_b=None):
        """ Evaluate the communication rates within CSP network.
        Given every frontent->file delay and distance.
        If continents are not specified - all continents will be considered.

        return: rate [km/s]
        """

        Xs, Ys = list(), list()
        for frontend in self.frontend_servers:
            for data_file in self.data_files:
                # Filter the relevant measurements
                if continent_a and continent_b:
                    if continent_a != frontend.continent or \
                            continent_b != data_file.continent:
                        continue

                distance = self.csp_distances[(frontend, data_file)]
                delay = self.csp_delays[(frontend, data_file)]

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

        self.csp_rates = rates
        return self.csp_rates


class DatasetUtils3Party(DatasetUtils):
    """
    This class represents the GeolocationUtils for the 3-party service.
    """

    # Don't override the __init__ method, as it is the same as the parent class.

    def compute_csp_delays_subtraction(self, cdgeb_utils_1party: DatasetUtils1Party):
        """
        Compute the round-trip times of the second hop (front-end to file)
        Using the subtraction method.
        """
        rtts_within_csp = dict()
        for frontend in self.frontend_servers:

            # frontend and frontend_1party have the same data center
            frontend_1party = [frontend_1party for frontend_1party in cdgeb_utils_1party.frontend_servers
                               if frontend.datacenter == frontend_1party.datacenter][0] or None

            closest_probe_in_1party = cdgeb_utils_1party.closest_probe_to_frontend[frontend_1party]
            closest_probe = self.closest_probe_to_frontend[frontend]

            if closest_probe_in_1party != closest_probe:
                print("[ERROR] Closest probes are not the same for 1-party and 3-party!")
                # TODO make sure that this scenario is handled in input validation function and not here.
                exit(0)

            closest_file_in_1party = cdgeb_utils_1party.closest_file_for_frontend[frontend]

            for data_file in self.data_files:
                rtts_within_csp[(frontend, data_file)] = \
                    self.measurements[(closest_probe.name, frontend.name, data_file.name)] - \
                    cdgeb_utils_1party.measurements[
                        (closest_probe_in_1party.name, frontend_1party.name, closest_file_in_1party.name)]

        self.csp_delays = {k: (v / 2) for k, v in rtts_within_csp.items()}
        return self.csp_delays

    def position_correction(self, coordinates: tuple[float, float]) -> DataCenter:
        """
        Return the closest possible location to the given coordinates.

        @param coordinates: Target's coordinates.
        """
        closest_possible_dc = min(self.possible_file_datacenters,
                                  key=lambda elem: haversine(coordinates, elem.coordinates))

        return closest_possible_dc
