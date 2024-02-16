import os
import sys
import numpy as np
from GeolocationUtils import GeolocationUtils
from GeolocationCSP import Geolocation
from common import Continent
from plot_map import MapBuilder
from rich.console import Console
from rich.table import Table

DATASET_FILE = 'full_dataset.csv'
PROBES_DATA_FILE = 'probes.csv'
SERVERS_DATA_FILE = 'servers.csv'
FRONTENDS_DATA_FILE = 'frontends.csv'
FILES_DATA_FILE = 'files.csv'
MAPPING_DATA_FILE = 'mapping.csv'


def check_files_exist(Input_dir):
    if not os.path.isfile(os.path.join(Input_dir, DATASET_FILE)):
        print("Missing file", DATASET_FILE)
        return False
    if not os.path.isfile(os.path.join(Input_dir, PROBES_DATA_FILE)):
        print("Missing file", PROBES_DATA_FILE)
        return False
    if not os.path.isfile(os.path.join(Input_dir, SERVERS_DATA_FILE)):
        print("Missing file", FRONTENDS_DATA_FILE)
        return False
    return True


def geolocation_main(Input_dir, Output_dir):
    # Create a Rich table for results
    table = Table(title="Geolocation Results", show_header=True, header_style="bold cyan")

    table.add_column("Taget", justify="center")
    table.add_column("Geolocation Error \[km]", justify="center")
    table.add_column("Closest Frontend", justify="center")
    table.add_column("Closest Frontend Error \[km]", justify="center")

    # Stage 0 - parse data
    # Load measurements from CSV
    measurements_to_all_targets = dict()
    with open(os.path.join(Input_dir, DATASET_FILE), 'r') as f:
        for line in f.readlines():
            line = line.replace('\r','').replace('\n','')
            probe, frontend, file = line.split(',')[0:3]
            measurements_to_all_targets[(probe, frontend, file)] = min([float(x) for x in line.split(',')[3:]])

    # Load other data
    probe_locations = dict()
    probes_continents = dict() # For later usage
    with open(os.path.join(Input_dir, PROBES_DATA_FILE), 'r') as f:
        for line in f.readlines():
            line = line.replace('\r','').replace('\n','')
            probe, lat, long, continent = line.split(',')[0:4]
            probe_locations[probe] = (float(lat), float(long))
            # probes_continents[probe] = Continent(continent)
    
    frontend_locations = dict()
    frontend_continents = dict()
    file_locations = dict()
    file_continents = dict()
    true_frontend_file_mapping = dict()
    with open(os.path.join(Input_dir, SERVERS_DATA_FILE), 'r') as f:
        for line in f.readlines():
            line = line.replace('\r','').replace('\n','')
            frontend, filename, lat, long, continent = line.split(',')[0:5]
            frontend_locations[frontend] = (float(lat), float(long))
            frontend_continents[frontend] = Continent(continent)
            file_locations[filename] = (float(lat), float(long))
            file_continents[filename] = Continent(continent)
            true_frontend_file_mapping[frontend] = filename

    true_file_frontend_mapping = {v:k for k,v in true_frontend_file_mapping.items()}

    # Stage 1 - Compute delays within CSP
    cdgeb_geolocation_utils = GeolocationUtils(
        true_file_frontend_mapping=true_file_frontend_mapping,
        probe_locations=probe_locations,
        frontend_locations=frontend_locations,
        frontend_continents=frontend_continents,
        file_locations=file_locations,
    )
    distance_map = cdgeb_geolocation_utils.build_distance_map()
    cdgeb_geolocation_utils.csp_distances = distance_map

    closets_probe_to_frontends = cdgeb_geolocation_utils.determine_closest_probes()
    cdgeb_geolocation_utils.closets_probe_to_frontends = closets_probe_to_frontends

    closest_file_for_frontend = cdgeb_geolocation_utils.determine_closest_files(measurements_to_all_targets)
    cdgeb_geolocation_utils.closest_file_for_frontend = closest_file_for_frontend

    rtts_within_csp = cdgeb_geolocation_utils.compute_csp_delays(measurements_to_all_targets)
    cdgeb_geolocation_utils.csp_delays = {k:v/2 for k,v in rtts_within_csp.items()}

    # Save results
    # TODO

    # Stage 2 - Compute transmission rates within CSP
    csp_general_rate = cdgeb_geolocation_utils.evaluate_csp_general_rate()
    csp_rates = cdgeb_geolocation_utils.evaluate_csp_rates()

    # Print results
    print("Rates within AWS (All measuremenets):", csp_general_rate)
    GeolocationUtils.pretty_print_rates(csp_rates)


    # Stages 3-5 - Geolocation
    # Create map of all geolocated targets
    map_all_targets = MapBuilder(f'all_targets', probe_locations, frontend_locations)
    map_all_targets.add_frontends()

    # Initialize a geolocator
    aws_geolocator = Geolocation(frontend_locations, csp_rates=csp_rates, frontend_continents=frontend_continents)

    results = dict()
    errors = list()
    for filename in file_locations:
        # Geolocate current file using measurements from other frontends
        frontend = true_file_frontend_mapping[filename]
        filename = true_frontend_file_mapping[frontend]
        delays_from_server = {frontend_name:cdgeb_geolocation_utils.csp_delays[(frontend_name, filename_d)] for (frontend_name, filename_d) in cdgeb_geolocation_utils.csp_delays.keys() \
                            if filename_d == filename}
        delays_from_server.pop(frontend)

        # Geolocation step
        estimated_location = aws_geolocator.geolocate_target(delays_from_server)
        closest_frontend = aws_geolocator.closest_frontend(estimated_location)
        
        # Make target-specific map file
        map_single_target = MapBuilder(f'{frontend}_estimated', probe_locations, frontend_locations)
        map_single_target.add_frontends()
        map_single_target.add_point(estimated_location, f'estimated-location-of-{frontend}')
        map_single_target.add_circle(estimated_location, GeolocationUtils.haversine(estimated_location, frontend_locations[frontend]))
        map_single_target.add_dashed_line(estimated_location, frontend_locations[frontend])
        map_single_target.add_line(estimated_location, frontend_locations[closest_frontend])
        map_single_target.save_map(Output_dir)

        # Calculate errors
        geolocation_error = GeolocationUtils.haversine(frontend_locations[frontend], estimated_location)
        closest_error = GeolocationUtils.haversine(frontend_locations[frontend], frontend_locations[closest_frontend])

        errors.append((geolocation_error, closest_error))
        table.add_row(frontend, 
                      str(round(geolocation_error, 2)), \
                      str(closest_frontend == frontend), \
                      str(round(closest_error, 2))
                    )
        
        map_all_targets.add_point(estimated_location, f'estimated-location-of-{frontend}',
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
    map_all_targets.save_map(Output_dir)


def main(Input_dir, Output_dir=None):
    if not Output_dir:
        Output_dir = os.path.join(Input_dir, 'out')

    if not check_files_exist(Input_dir):
        # Already logged inside
        return
    
    # Create output directory if not exist
    if not os.path.isdir(Output_dir):
       os.makedirs(Output_dir)
    
    geolocation_main(Input_dir, Output_dir)


if __name__ == '__main__':
    Input_dir = 'example'
    main(Input_dir)
