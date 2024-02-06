import localization as lx
import numpy as np
from scipy.optimize import minimize
from common import aws_general_rate
from common import Continent, aws_rates, frontend_continents # for content-aware


class Geolocation:
    @classmethod
    def delay_to_distance_continent_aware(cls, delay: float, src_continent: Continent, target_assumed_continent: Continent) -> float:
        """
        Converts measured single-direction delay of data within AWS backbone to distances
        according to the transmission rate computed from advanced. (See front-file scatterplot)
        
        @param delay: single-direction delay in seconds
        @param src_continent: continent of the frontend server
        @param target_assumed_continent: assumed continent of the file, which impacts the rate constansts
        return: distance in kilometers
        """
        return delay * aws_rates[(src_continent, target_assumed_continent)]

    @classmethod
    def delay_to_distance(cls, delay: float) -> float:
        """
        Converts measured single-direction delay of data within AWS backbone to distances
        according to the transmission rate computed from advanced. (See front-file scatterplot)
        
        @param delay: single-direction delay in seconds
        return: distance in kilometers
        """
        # Divide by 2 to get the time for single direction
        return delay * aws_general_rate

    @classmethod
    def _geolocate_using_Localization(cls, fe_locations, distances):
        """
        Unfortunately, this doesn't work well. Prefer using the other method.
        """
        # Create and populate dataset for the geolocation module
        P = lx.Project(mode='Earth1', solver='LSE')
        [P.add_anchor(fe, fe_locations[fe]) for fe in distances]

        t, label = P.add_target()
        # Note: following function uses meters
        [t.add_measure(fe, 1000*distances[fe]) for fe in distances] 

        P.solve()
        return t.loc.x, t.loc.y

    @classmethod
    def _geolocate_using_scipy(cls, fe_locations, distances):
        """
        Co-Author: Daniel
        """
        def loss_function(current_guess, known_distances, positions):
            distances_from_guess = np.array([cls.haversine(current_guess, probe) for probe in positions])
            return np.sum((distances_from_guess - known_distances) ** 2)
        
        def triangulate(positions, distances):
            initial_guess = np.mean(positions, axis=0)
            # Note: reverted as for some reason many targets where estimated to the bouneries themselves (e.g. [-90,-180]),
            # whereas the estimation without the bounderies was correct.
            # bounds = [(-90, 90), (-180, 180)] # lat, lon boundaries
            result = minimize(loss_function, initial_guess, args=(distances, positions), 
                            #   bounds=bounds, 
                              method='L-BFGS-B', options={'disp': False})
            return result.x
        
        fe_positions = [fe_locations[fe] for fe in distances]
        distances_from_fes = list(distances.values())

        def normalize_coordinates(coord_unnormalized):
            """
            Normalizes a given coordinates to the ranges: lat = [-90, 90], lon = [-180, 180].
            Please read the previous note.
            """
            lat1, lon1 = coord_unnormalized[0], coord_unnormalized[1]
            lat2 = (lat1 + 90) % 180 - 90
            lon2 = (lon1 + 180) % 360 - 180
            return (lat2, lon2)

        target = triangulate(np.array(fe_positions), np.array(distances_from_fes))
        return normalize_coordinates(target)

    @classmethod
    def geolocate_target(cls, measurements: dict, fe_locations: dict):
        """
        Given single-direction delay measurements from multiple front-end servers
        with known locations to a file, geolocate the file.
        
        @param measurements: dict of front-end names and their *single-direction delays* (not RTT!) to the file
        @param fe_locations: dict of front-end names and their (lat, long) coordinates
        return: (lat, long) coordinates of the file
        """
        assert all(key in fe_locations for key in measurements), "Inputs do not match"

        assumed_closest_frontend = min(measurements, key=measurements.get)
        target_assumed_continent = frontend_continents[assumed_closest_frontend]

        # Convert time measurements to distances
        distances = {fe:cls.delay_to_distance_continent_aware(delay, frontend_continents[fe], target_assumed_continent) \
                     for fe, delay in measurements.items()}

        # return cls._geolocate_using_Localization(fe_locations, distances)
        return cls._geolocate_using_scipy(fe_locations, distances)
    
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
    
    @classmethod
    def closest_frontend(cls, target: tuple[float, float], fe_locations: dict) -> tuple:
        closest_fe = min(fe_locations.items(), key=lambda elem: cls.haversine(target, elem[1]))

        return closest_fe[0]
    
    @classmethod
    def test_geolocate_using_scipy(cls):
        from common import frontendId2Name, real_fe_for_file, aws_distances, frontend_locations
        from plot_map import MapBuilder
        
        for target_frontend_id in range(1, 17+1):
            target_frontend = frontendId2Name(target_frontend_id)
            # Build measurements setup using real known distances:
            dists_from_server = {src_frontend:aws_distances[(src_frontend, target_filename)] for (src_frontend, target_filename) in aws_distances.keys() \
                                if real_fe_for_file[target_filename] == target_frontend}
            dists_from_server.pop(target_frontend)

            target = cls._geolocate_using_scipy(frontend_locations, dists_from_server)
            
            map = MapBuilder(f'true_distances_{target_frontend_id}')
            map.add_frontends()
            map.add_point(target, f'estimated-location-of-server-{target_frontend_id}')
            map.add_circle(target, Geolocation.haversine(target, frontend_locations[target_frontend]))
            map.save_map()

## test _geolocate_using_scipy
Geolocation.test_geolocate_using_scipy()
