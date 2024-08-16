import numpy as np
from scipy.optimize import minimize
from CDGeB1.data_classes import Continent, FrontEnd, DataFile, DataCenter
from CDGeB1.CloudServiceUtils import haversine


class MultilaterationUtils:
    """
    This class is a utility class for geolocating a target using multilateration.
    """

    def __init__(self, frontend_servers: dict,
                 csp_general_rate: float = None, csp_rates: dict = None):
        """
        @param frontend_servers: dict of front-end names and their (lat, long) coordinates.
        @param csp_general_rate: a float value of transmission rate within the CSP's network. Optional.
        @param csp_rates: dict of (Continent, Continent) and their corresponding transmission rate. Optional (if csp_general_rate is supplied).
        @param frontend_continents: a dict mapping between front-end servers and their Continent. Required if csp_rates supplied.
        """

        self.frontend_server = frontend_servers
        self.csp_general_rate = csp_general_rate
        self.csp_rates = csp_rates

    def delay_to_distance_continent_aware(self, delay: float, src_continent: Continent,
                                          target_assumed_continent: Continent) -> float:
        """
        Converts measured single-direction delay of data within CSP backbone to distances
        according to the transmission rate computed from advanced. (See front-file scatterplot)
        
        @param delay: single-direction delay in seconds
        @param src_continent: continent of the frontend server
        @param target_assumed_continent: assumed continent of the file, which impacts the rate constansts
        return: distance in kilometers
        """

        return delay * self.csp_rates[(src_continent, target_assumed_continent)]

    def delay_to_distance(self, delay: float) -> float:
        """
        Converts measured single-direction delay of data within CSP backbone to distances
        according to the transmission rate computed from advanced. (See front-file scatterplot)
        
        @param delay: single-direction delay in seconds
        return: distance in kilometers
        """

        return delay * self.csp_general_rate

    def _geolocate_using_scipy(self, distances: dict[FrontEnd, float]):
        """
        This method uses scipy's minimize to geolocate the target.
        Co-Author: Daniel
        """

        def normalize_coordinates(coord_unnormalized):
            """
            Normalizes a given coordinates to the ranges: lat = [-90, 90], lon = [-180, 180].
            Please read the note in multilateraion.
            """
            lat1, lon1 = coord_unnormalized[0], coord_unnormalized[1]
            lat2 = (lat1 + 90) % 180 - 90
            lon2 = (lon1 + 180) % 360 - 180
            return (lat2, lon2)

        def loss_function(current_guess, known_distances, positions):
            distances_from_guess = np.array([haversine(current_guess, probe) for probe in positions])
            return np.sum((distances_from_guess - known_distances) ** 2)

        def multilateration(positions, distances):
            # initial_guess = np.mean(positions, axis=0)
            initial_guess = positions[np.argmin(distances)]
            # Note: reverted as for some reason many targets where estimated to the bouneries themselves (e.g. [-90,-180]),
            # whereas the estimation without the bounderies was correct.
            # bounds = [(-90, 90), (-180, 180)] # lat, lon boundaries
            result = minimize(loss_function, initial_guess, args=(distances, positions),
                              #   bounds=bounds,
                              method='L-BFGS-B', options={'disp': False})
            return result.x

        distances_from_fes = list(distances.values())
        feontend_locations = [frontend.coordinates for frontend in distances]

        target = multilateration(np.array(feontend_locations), np.array(distances_from_fes))
        return normalize_coordinates(target)

    def geolocate_target(self, measurements_to_target: dict[FrontEnd, float]):
        """
        Given single-direction delay measurements from multiple front-end servers
        with known locations to a file, geolocate the file.
        
        @param measurements_to_target: dict of front-end names and their *single-direction delays* (not RTT!) to a single target file
        
        return: (lat, long) coordinates of the file
        """

        # assert all(any(frontend.name == frontend_name for frontend in self.frontend_server)
        #            for frontend_name in measurements_to_target), "Inputs do not match (measurements_to_target, fe_locations)"

        assert all(frontend in self.frontend_server for frontend in
                   measurements_to_target), "Inputs do not match (measurements_to_target, fe_locations)"

        assumed_closest_frontend = min(measurements_to_target, key=measurements_to_target.get)
        target_assumed_continent = assumed_closest_frontend.continent

        # Convert time measurements to distances
        # distances = {fe:self.delay_to_distance(delay) for fe, delay in measurements_to_target.items()}
        distances = {
            frontend: self.delay_to_distance_continent_aware(delay, frontend.continent, target_assumed_continent)
            for frontend, delay in measurements_to_target.items()}

        return self._geolocate_using_scipy(distances)

    def geolocate_target_from_distances(self, distances: dict[FrontEnd, float]):
        """
        Similar to geolocate_target, but uses given distances instead of delay measurements.
        @param distances: dict(frontend: distance)
        """
        # assert all(any(frontend.name == frontend_name for frontend in self.frontend_server)
        #            for frontend_name in distances), "Inputs do not match (distances, fe_locations)"
        assert all(
            frontend in self.frontend_server for frontend in distances), "Inputs do not match (distances, fe_locations)"

        return self._geolocate_using_scipy(distances)


class ProfilingUtils:
    """
    This class is a utility class for geolocating a target using profiling-based method.
    Note that 1-st party fingerprints might contain more datacenters than in the 3-party case.
    """

    type Fingerprint = dict[DataCenter, float]
    type FeatureVector = dict[DataCenter, float]

    def __init__(self, datacenters: list[DataCenter], fingerprints: dict[DataCenter, Fingerprint] = None):
        self.csp_datacenters = datacenters
        self.csp_fingerprints = fingerprints

    def create_1party_fingerprints(self, measurements_2hop: dict[tuple[FrontEnd, DataFile], float]) \
            -> dict[DataCenter, Fingerprint]:
        """
        Given measurements from 2-hop measurements, create fingerprints for each datacenter.
        """

        fingerprints = dict()
        for (frontend, file), delay in measurements_2hop.items():
            if frontend.datacenter not in fingerprints:
                fingerprints[frontend.datacenter] = dict()
            fingerprints[frontend.datacenter][file.datacenter] = delay

        self.csp_fingerprints = fingerprints
        return fingerprints

    def evaluate_feature_vectors(self, measurements_to_target: dict[FrontEnd, float]) \
            -> FeatureVector:
        """
        Given measurements to a target, evaluate the feature vector.
        """

        feature_vector = dict()
        for frontend, delay in measurements_to_target.items():
            feature_vector[frontend.datacenter] = delay

        return feature_vector

    def match_feature_vector_to_fingerprint(self, feature_vector: FeatureVector,
                                            possible_file_datacenters: list[DataCenter]) -> DataCenter:
        """
        Given a feature vector, match it to the most similar fingerprint, and return the associated datacenter.
        """

        possible_fingerprints = {datacenter: self.csp_fingerprints[datacenter] for datacenter in
                                 possible_file_datacenters}
        feature_vector_reduced = np.array([feature_vector[datacenter] for datacenter in possible_file_datacenters])

        def similarity(fingerprint) -> float:
            """
            Compute the similarity between a fingerprint and a feature vector.
            """

            # Reason: the fingerprint might contain more datacenters than the feature vector
            # and also, this vector must be in the same order as the feature_vector_reduced
            fingerprint_reduced = np.array([fingerprint.get[datacenter] for datacenter in possible_file_datacenters])

            # return np.linalg.norm(fingerprint_reduced - feature_vector_reduced)
            return np.dot(fingerprint_reduced, feature_vector_reduced) / (
                        np.linalg.norm(fingerprint_reduced) * np.linalg.norm(feature_vector_reduced))

        # Find the most similar fingerprint
        best_match = max(possible_fingerprints, key=lambda x: similarity(possible_fingerprints[x]))

        return best_match
