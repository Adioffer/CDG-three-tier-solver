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


def geolocate_frontend(frontend):
    filename = real_file_for_fe[frontend]
    delays_from_server = {frontend_name:aws_delays[(frontend_name, filename_d)] for (frontend_name, filename_d) in aws_delays.keys() \
                        if filename_d == filename}
    delays_from_server.pop(frontend)    
    
    # Geolocation
    estimated_location = Geolocation.geolocate_target(delays_from_server, frontend_locations)
    closest_frontend = Geolocation.closest_frontend(estimated_location, frontend_locations)

    # Make map file
    map = MapBuilder(f'{frontend}_estimated')
    map.add_frontends()
    map.add_point(estimated_location, f'estimated-location-of-{frontend}')
    map.add_circle(estimated_location, Geolocation.haversine(estimated_location, frontend_locations[frontend]))
    map.save_map()

    return estimated_location, closest_frontend

if __name__ == '__main__':
    # Create a Rich table
    table = Table(title="Geolocation Results", show_header=True, header_style="bold cyan")

    table.add_column("Taget", justify="center")
    table.add_column("Geolocation Error \[km]", justify="center")
    table.add_column("Closest Frontend", justify="center")
    table.add_column("Closest Frontend Error \[km]", justify="center")

    results = dict()
    errors = list()
    for frontend in cdgeb_frontends:
        estimated_location, closest_frontend = geolocate_frontend(frontend)

        geolocation_error = Geolocation.haversine(frontend_locations[frontend], estimated_location)
        closest_error = Geolocation.haversine(frontend_locations[frontend], frontend_locations[closest_frontend])

        errors.append((geolocation_error, closest_error))
        table.add_row(frontend, 
                      str(round(geolocation_error, 2)), \
                      str(closest_frontend == frontend), \
                      str(round(closest_error, 2))
                    )

    # Print the table
    console = Console()
    console.print(table)

    mse_error = np.sqrt(np.mean(np.square([err[0] for err in errors])))
    print("Geolocation Error (MSE): ", round(mse_error, 2), "[km]")
    mse_error = np.sqrt(np.mean(np.square([err[1] for err in errors])))
    print("Closest Geolocation Error (MSE): ", round(mse_error, 2), "[km]")
    print()
