import localization as lx
import numpy as np
from scipy.optimize import minimize
from common import Continent # for content-aware


class Geolocation:
    @classmethod
    def haversine(cls, coord1, coord2):
        lat1, lon1 = np.radians(coord1)
        lat2, lon2 = np.radians(coord2)
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
        distance = 6371.0 * c  # Radius of Earth in kilometers

        return distance
    
    def __init__(self, fe_locations: dict,
                 csp_general_rate: float=None, csp_rates: dict=None, frontend_continents: dict =None):
        """
        @param fe_locations: dict of front-end names and their (lat, long) coordinates
        ... TODO
        """
        
        self.fe_locations = fe_locations
        self.frontend_continents = frontend_continents
        self.csp_general_rate = csp_general_rate
        self.csp_rates = csp_rates

    def delay_to_distance_continent_aware(self, delay: float, src_continent: Continent, target_assumed_continent: Continent) -> float:
        """
        Converts measured single-direction delay of data within AWS backbone to distances
        according to the transmission rate computed from advanced. (See front-file scatterplot)
        
        @param delay: single-direction delay in seconds
        @param src_continent: continent of the frontend server
        @param target_assumed_continent: assumed continent of the file, which impacts the rate constansts
        return: distance in kilometers
        """
        return delay * self.csp_rates[(src_continent, target_assumed_continent)]

    def delay_to_distance(self, delay: float) -> float:
        """
        Converts measured single-direction delay of data within AWS backbone to distances
        according to the transmission rate computed from advanced. (See front-file scatterplot)
        
        @param delay: single-direction delay in seconds
        return: distance in kilometers
        """
        # Divide by 2 to get the time for single direction
        return delay * self.csp_general_rate

    def _geolocate_using_Localization(self, distances):
        """
        Unfortunately, this doesn't work well. Prefer using the other method.
        """
        # Create and populate dataset for the geolocation module
        P = lx.Project(mode='Earth1', solver='LSE')
        [P.add_anchor(fe, self.fe_locations[fe]) for fe in distances]

        t, label = P.add_target()
        # Note: following function uses meters
        [t.add_measure(fe, 1000*distances[fe]) for fe in distances] 

        P.solve()
        return t.loc.x, t.loc.y

    def _geolocate_using_scipy(self, distances):
        """
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
            distances_from_guess = np.array([self.haversine(current_guess, probe) for probe in positions])
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

    def geolocate_target(self, measurements: dict):
        """
        Given single-direction delay measurements from multiple front-end servers
        with known locations to a file, geolocate the file.
        
        @param measurements: dict of front-end names and their *single-direction delays* (not RTT!) to the file
        
        return: (lat, long) coordinates of the file
        """

        assert all(frontend in self.fe_locations \
                   for frontend in measurements), "Inputs do not match (measurements, fe_locations)"
        
        if self.frontend_continents:
            assert all(frontend in self.frontend_continents \
                       for frontend in measurements), "Inputs do not match (measurements, frontend_continents)"

        assumed_closest_frontend = min(measurements, key=measurements.get)
        target_assumed_continent = self.frontend_continents[assumed_closest_frontend]

        # Convert time measurements to distances
        # distances = {fe:self.delay_to_distance(delay) for fe, delay in measurements.items()}
        distances = {fe:self.delay_to_distance_continent_aware(delay, self.frontend_continents[fe], target_assumed_continent) for fe, delay in measurements.items()}

        # return self._geolocate_using_Localization(distances)
        return self._geolocate_using_scipy(distances)

    def geolocate_target_from_distances(self, distances: dict):
        """
        Similar to geolocate_target, but uses given distances instead of delay measurements.
        distances: dict(frontend: distance)
        """
        assert all(frontend in self.fe_locations \
                   for frontend in distances), "Inputs do not match (distances, fe_locations)"

        # return self._geolocate_using_Localization(distances)
        return self._geolocate_using_scipy(distances)
    
    def closest_frontend(self, target: tuple[float, float]) -> tuple:
        closest_fe = min(self.fe_locations.items(), key=lambda elem: self.haversine(target, elem[1]))

        return closest_fe[0]
    
    def test_geolocate_using_scipy(self):
        from common import frontendId2Name, true_fe_for_file, aws_distances, frontend_locations
        from plot_map import MapBuilder
        
        for target_frontend_id in range(1, 17+1):
            target_frontend = frontendId2Name(target_frontend_id)
            # Build measurements setup using real known distances:
            dists_from_server = {src_frontend:aws_distances[(src_frontend, target_filename)] for (src_frontend, target_filename) in aws_distances.keys() \
                                if true_fe_for_file[target_filename] == target_frontend}
            dists_from_server.pop(target_frontend)

            target = self._geolocate_using_scipy(dists_from_server)
            
            map = MapBuilder(f'true_distances_{target_frontend_id}')
            map.add_frontends()
            map.add_point(target, f'estimated-location-of-server-{target_frontend_id}')
            map.add_circle(target, Geolocation.haversine(target, frontend_locations[target_frontend]))
            map.save_map()

## test _geolocate_using_scipy
# Geolocation.test_geolocate_using_scipy()
