import numpy as np
from scipy.optimize import minimize
from CDGeB1.common import Continent # for content-aware
from CDGeB1.GeolocationUtils import GeolocationUtils


class Geolocation():
    def __init__(self, fe_locations: dict,
                 csp_general_rate: float=None, csp_rates: dict=None, frontend_continents: dict =None):
        """
        @param fe_locations: dict of front-end names and their (lat, long) coordinates.
        @param csp_general_rate: a float value of transmission rate within the CSP's network. Optional.
        @param csp_rates: dict of (Continent, Continent) and their corresponding transmission rate. Optional (if csp_general_rate is supplied).
        @param frontend_continents: a dict mapping between front-end servers and their Continent. Required if csp_rates supplied.
        """
        
        self.fe_locations = fe_locations
        self.frontend_continents = frontend_continents
        self.csp_general_rate = csp_general_rate
        self.csp_rates = csp_rates

    def delay_to_distance_continent_aware(self, delay: float, src_continent: Continent, target_assumed_continent: Continent) -> float:
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
        # Divide by 2 to get the time for single direction
        return delay * self.csp_general_rate

    def _geolocate_using_scipy(self, distances):
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
            distances_from_guess = np.array([GeolocationUtils.haversine(current_guess, probe) for probe in positions])
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
        fe_positions = [self.fe_locations[fe] for fe in distances]

        target = multilateration(np.array(fe_positions), np.array(distances_from_fes))
        return normalize_coordinates(target)

    def geolocate_target(self, measurements_to_target: dict):
        """
        Given single-direction delay measurements from multiple front-end servers
        with known locations to a file, geolocate the file.
        
        @param measurements_to_target: dict of front-end names and their *single-direction delays* (not RTT!) to a single target file
        
        return: (lat, long) coordinates of the file
        """

        assert all(frontend in self.fe_locations \
                   for frontend in measurements_to_target), "Inputs do not match (measurements_to_target, fe_locations)"
        
        if self.frontend_continents:
            assert all(frontend in self.frontend_continents \
                       for frontend in measurements_to_target), "Inputs do not match (measurements_to_target, frontend_continents)"

        assumed_closest_frontend = min(measurements_to_target, key=measurements_to_target.get)
        target_assumed_continent = self.frontend_continents[assumed_closest_frontend]

        # Convert time measurements to distances
        # distances = {fe:self.delay_to_distance(delay) for fe, delay in measurements_to_target.items()}
        distances = {fe:self.delay_to_distance_continent_aware(delay, self.frontend_continents[fe], target_assumed_continent) for fe, delay in measurements_to_target.items()}

        return self._geolocate_using_scipy(distances)

    def geolocate_target_from_distances(self, distances: dict):
        """
        Similar to geolocate_target, but uses given distances instead of delay measurements.
        @param distances: dict(frontend: distance)
        """
        assert all(frontend in self.fe_locations \
                   for frontend in distances), "Inputs do not match (distances, fe_locations)"

        return self._geolocate_using_scipy(distances)
    
    def closest_frontend(self, target: tuple[float, float]) -> tuple:
        """
        Return the closest front-end server to the given coordinates.
        
        @param target: Target's coordinates.
        """
        closest_fe = min(self.fe_locations.items(), key=lambda elem: GeolocationUtils.haversine(target, elem[1]))

        return closest_fe[0]
    