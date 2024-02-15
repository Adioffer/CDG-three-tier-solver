from Geolocation_CSP import Geolocation
import numpy as np
from plot_map import MapBuilder
from rich.console import Console
from rich.table import Table


def geolocate_single_target(aws_geolocator: Geolocation, frontend: str, csp_delays: dict, csp_distances: dict, true_locations: dict, true_file_for_fe: dict):
    filename = true_file_for_fe[frontend]
    delays_from_server = {frontend_name:csp_delays[(frontend_name, filename_d)] for (frontend_name, filename_d) in csp_delays.keys() \
                        if filename_d == filename}
    delays_from_server.pop(frontend)    
    
    # Geolocation
    if True:
        # Geolocation from delays
        estimated_location = aws_geolocator.geolocate_target(delays_from_server)
        map_name_appender = ''
    else:
        # Geolocation from distances
        map_name_appender = '_from_distances'
        dists_from_server = {src_frontend:csp_distances[(src_frontend, target_filename)] for (src_frontend, target_filename) in csp_distances.keys() \
                                  if src_frontend != frontend and true_fe_for_file[target_filename] == frontend}
        estimated_location = aws_geolocator.geolocate_target_from_distances(dists_from_server)
    
    closest_frontend = aws_geolocator.closest_frontend(estimated_location)

    # Make map file
    map = MapBuilder(f'{frontend}_estimated' + map_name_appender)
    map.add_frontends()
    map.add_point(estimated_location, f'estimated-location-of-{frontend}')
    map.add_circle(estimated_location, Geolocation.haversine(estimated_location, true_locations[frontend]))
    map.save_map()

    return estimated_location, closest_frontend

def geolocation_main(csp_delays, csp_distances, frontends, frontend_locations, csp_general_rate, csp_rates, frontend_continents, true_file_for_fe):
    # Create a Rich table for results
    table = Table(title="Geolocation Results", show_header=True, header_style="bold cyan")

    table.add_column("Taget", justify="center")
    table.add_column("Geolocation Error \[km]", justify="center")
    table.add_column("Closest Frontend", justify="center")
    table.add_column("Closest Frontend Error \[km]", justify="center")

    # Create map of all geolocated targets
    map = MapBuilder(f'all_targets')
    map.add_frontends()

    # Initialize a geolocator
    aws_geolocator = Geolocation(frontend_locations, csp_general_rate=csp_general_rate, csp_rates=csp_rates, frontend_continents=frontend_continents)

    results = dict()
    errors = list()
    for frontend in frontends:
        estimated_location, closest_frontend = geolocate_single_target(aws_geolocator, frontend, csp_delays, csp_distances, frontend_locations, true_file_for_fe)

        geolocation_error = Geolocation.haversine(frontend_locations[frontend], estimated_location)
        closest_error = Geolocation.haversine(frontend_locations[frontend], frontend_locations[closest_frontend])

        errors.append((geolocation_error, closest_error))
        table.add_row(frontend, 
                      str(round(geolocation_error, 2)), \
                      str(closest_frontend == frontend), \
                      str(round(closest_error, 2))
                    )
        
        map.add_point(estimated_location, f'estimated-location-of-{frontend}',
                      color="green" if closest_frontend == frontend else "red")

    # Print the table
    console = Console()
    console.print(table)

    rmse_error = np.sqrt(np.mean(np.square([err[0] for err in errors])))
    print("Geolocation Error (RMSE): ", round(rmse_error, 2), "[km]")
    rmse_error = np.sqrt(np.mean(np.square([err[1] for err in errors])))
    print("Closest Geolocation Error (RMSE): ", round(rmse_error, 2), "[km]")
    print()

    # Save the map
    map.save_map()

def geolocation_main_bgu():
    from common import cdgeb_probes, cdgeb_frontends, cdgeb_files
    from common import frontend_locations, true_file_for_fe, true_file_for_fe
    from common import aws_distances, aws_delays
    from common import aws_general_rate, aws_rates, frontend_continents
    geolocation_main(aws_delays, aws_distances, cdgeb_frontends, frontend_locations, aws_general_rate, aws_rates, frontend_continents, true_file_for_fe)

def geolocation_main_fujitsu():
    pass
    # TODO

if __name__ == '__main__':
    geolocation_main_bgu()
    # geolocation_main_fujitsu()
