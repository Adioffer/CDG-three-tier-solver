from geolocation_in_aws import Geolocation
import numpy as np
from sklearn.metrics import mean_squared_error
from plot_map import MapBuilder
from rich.console import Console
from rich.table import Table

from common import cdgeb_probes, cdgeb_frontends, cdgeb_files
from common import probeId2Name, frontendId2Name, fileId2Name
from common import frontend_locations, real_fe_for_file, real_file_for_fe
from common import aws_distances, aws_delays


def _geolocate_frontend(frontend):
    filename = real_file_for_fe[frontend]
    delays_from_server = {frontend_name:aws_delays[(frontend_name, filename_d)] for (frontend_name, filename_d) in aws_delays.keys() \
                        if filename_d == filename}
    delays_from_server.pop(frontend)    
    
    # Geolocation
    if True:
        # Geolocation from delays
        estimated_location = Geolocation.geolocate_target(frontend_locations, delays_from_server)
        map_name_appender = ''
    else:
        # Geolocation from distances
        map_name_appender = '_from_distances'
        dists_from_server = {src_frontend:aws_distances[(src_frontend, target_filename)] for (src_frontend, target_filename) in aws_distances.keys() \
                                  if src_frontend != frontend and real_fe_for_file[target_filename] == frontend}
        estimated_location = Geolocation.geolocate_target_from_distances(frontend_locations, dists_from_server)
    
    closest_frontend = Geolocation.closest_frontend(frontend_locations, estimated_location)

    # Make map file
    map = MapBuilder(f'{frontend}_estimated' + map_name_appender)
    map.add_frontends()
    map.add_point(estimated_location, f'estimated-location-of-{frontend}')
    map.add_circle(estimated_location, Geolocation.haversine(estimated_location, frontend_locations[frontend]))
    map.save_map()

    return estimated_location, closest_frontend

if __name__ == '__main__':
    # Create a Rich table for results
    table = Table(title="Geolocation Results", show_header=True, header_style="bold cyan")

    table.add_column("Taget", justify="center")
    table.add_column("Geolocation Error \[km]", justify="center")
    table.add_column("Closest Frontend", justify="center")
    table.add_column("Closest Frontend Error \[km]", justify="center")

    # Create map of all geolocated targets
    map = MapBuilder(f'all_targets')
    map.add_frontends()


    results = dict()
    errors = list()
    for frontend in cdgeb_frontends:
        estimated_location, closest_frontend = _geolocate_frontend(frontend)

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
