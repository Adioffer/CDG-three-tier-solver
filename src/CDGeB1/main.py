import os
import sys
import csv
import numpy as np
from rich.console import Console
from rich.table import Table

from CDGeB1.CloudServiceUtils import *
from CDGeB1.GeolocationUtils import MultilaterationUtils
from CDGeB1.data_classes import *
from CDGeB1.plot_map import MapBuilder
from CDGeB1.parsers import *

import itertools
import random
import pickle

MEASUREMENT_FILE_1PARTY = 'measurements-1party.csv'
SERVERS_DATA_FILE_1PARTY = 'servers-1party.csv'
DATACENTERS_FILE = 'datacenters.csv'
MEASUREMENT_FILE_3PARTY = 'measurements-3party.csv'
SERVERS_DATA_FILE_3PARTY = 'servers-3party.csv'
SOLUTION_DATA_FILE = 'solution.csv'

MEASUREMENT_PROBES = 0
MEASUREMENT_FRONTENDS = 1
MEASUREMENT_FILES = 2

MEASUREMENT_FILE_ENTRY_LENGTH = 23
SERVER_FILE_FULL_ENTRY_LENGTH = 4
DATACENTER_FILE_ENTRY_LENGTH = 5
SOLUTION_FILE_ENTRY_LENGTH = 2

COORDINATES_LENGTH = 2

METHOD_SUBTRACTION = "subtraction"
METHOD_OPTIMIZATION = "optimizer"


def parse_input_files(input_dir, testing_mode=False):
    datacenters, possible_file_datacenters = parse_datacenters(input_dir)

    probes_1party, frontends_1party, files_1party = parse_servers_1party(input_dir, datacenters)
    measurements_1party = parse_measurements_1party(input_dir, probes_1party, frontends_1party, files_1party)

    probes_3party, frontends_3party, files_3party = parse_servers_3party(input_dir, datacenters)
    measurements_3party = parse_measurements_3party(input_dir, probes_3party, frontends_3party, files_3party)

    true_file_datacenter_mapping_3party = None
    if testing_mode:
        true_file_datacenter_mapping_3party = parse_solution(input_dir, datacenters, files_3party)

    cdgeb_utils_1party = DatasetUtils1Party(
        measurements=measurements_1party,
        datacenters=datacenters,
        probe_clients=probes_1party,
        frontend_servers=frontends_1party,
        data_files=files_1party,
    )

    cdgeb_utils_3party = DatasetUtils3Party(
        measurements=measurements_3party,
        datacenters=datacenters,
        probe_clients=probes_3party,
        frontend_servers=frontends_3party,
        data_files=files_3party,
        possible_file_datacenters=possible_file_datacenters,
        solutions=true_file_datacenter_mapping_3party,
    )

    return cdgeb_utils_1party, cdgeb_utils_3party


def validate_input_files(cdgeb_utils_1party, cdgeb_utils_3party, method, testing_mode):
    if method == METHOD_SUBTRACTION:
        # Each datacenter utilized by 3Party must be present in 1Party
        if not set(cdgeb_utils_3party.datacenters) <= set(cdgeb_utils_1party.datacenters):
            print("[ERROR] Datacenters in 3Party not found in 1Party")
            return False

        # Both 1Party and 3Party must have the same "closest" probe clients
        if not set(cdgeb_utils_3party.closest_probe_to_frontend.values()) <= set(
                cdgeb_utils_1party.closest_probe_to_frontend.values()):
            print("[ERROR] 1Party and 3Party don't share the same closest probe clients")
            return False

    if testing_mode:
        # Each file in 3Party must have a solution
        if not set(cdgeb_utils_3party.data_files) <= set(cdgeb_utils_3party.solutions):
            print("[ERROR] Some files in 3Party don't have solutions")
            return False

        # Each file in 3Party must be located in a possible datacenter
        if not set(cdgeb_utils_3party.solutions.values()) <= set(cdgeb_utils_3party.possible_file_datacenters):
            print("[ERROR] Some files in 3Party solution don't reside in possible datacenters")
            return False

    return True


def learn_from_data(cdgeb_utils_1party, cdgeb_utils_3party, method, testing_mode=False):
    # Stage - Evaluate second-hop RTTs and CSP transmission rates
    if method == METHOD_SUBTRACTION:
        cdgeb_utils_1party.compute_csp_delays_subtraction()
        csp_general_rate = cdgeb_utils_1party.evaluate_csp_general_rate()
        csp_rates = cdgeb_utils_1party.evaluate_csp_rates()

        # print rates
        print()
        pretty_print_rates(csp_rates)
        print("Rates within CSP (All measuremenets):", csp_general_rate)
        print()

        cdgeb_utils_3party.csp_rates = csp_rates
        cdgeb_utils_3party.compute_csp_delays_subtraction(cdgeb_utils_1party)

    elif method == METHOD_OPTIMIZATION:
        cdgeb_utils_1party.compute_csp_delays_optimizer()
        csp_general_rate = cdgeb_utils_1party.evaluate_csp_general_rate()
        csp_rates = cdgeb_utils_1party.evaluate_csp_rates()

        # print rates
        print()
        pretty_print_rates(csp_rates)
        print("Rates within CSP (All measuremenets):", csp_general_rate)
        print()

        cdgeb_utils_3party.csp_rates = csp_rates
        cdgeb_utils_3party.compute_csp_delays_optimizer()
    else:
        print("[ERROR] Invalid method:", method)
        return

    return csp_rates


def are_tables_equal(table1, table2):
    if table1.title != table2.title:
        return False
    if len(table1.columns) != len(table2.columns):
        return False
    for col1, col2 in zip(table1.columns, table2.columns):
        if col1.header != col2.header:
            return False
    rows1 = list(table1.rows)
    rows2 = list(table2.rows)
    if len(rows1) != len(rows2):
        return False
    for row1, row2 in zip(rows1, rows2):
        if row1 != row2:
            return False
    return True


def geolocate_from_data(output_dir, cdgeb_utils_1party, cdgeb_utils_3party, method, testing_mode):
    if testing_mode:
        # Create a Rich table for results
        table = Table(title="Geolocation Results", show_header=True, header_style="bold cyan")

        table.add_column("File Name", justify="center")
        table.add_column("Taget", justify="center")
        table.add_column("Geolocation Error [km]", justify="center")
        table.add_column("Closest Frontend", justify="center")
        table.add_column("Closest Frontend Error [km]", justify="center")
    else:
        table = Table(title="Geolocation Results", show_header=True, header_style="bold cyan")

        table.add_column("File Name", justify="center")
        table.add_column("Assumed Datacenter", justify="center")

    # Stages - Geolocation
    # Create map of all geolocated targets
    map_all_targets = MapBuilder("all_targets", cdgeb_utils_3party.probe_clients,
                                 cdgeb_utils_3party.possible_file_datacenters)
    map_all_targets.add_datacenter()

    # Initialize a geolocator
    if method == METHOD_SUBTRACTION or method == METHOD_OPTIMIZATION:
        csp_geolocator = MultilaterationUtils(cdgeb_utils_3party.frontend_servers,
                                              csp_rates=cdgeb_utils_3party.csp_rates)
    else:
        print("[ERROR] Invalid method:", method)
        return

    errors = []
    for target_file in cdgeb_utils_3party.data_files:

        if method == METHOD_SUBTRACTION or method == METHOD_OPTIMIZATION:
            # Prepare delays from front-end servers for the target file.
            # Remove delays from front-end server in the same datacenter.
            delays_from_server = {k[0]: v for (k, v) in cdgeb_utils_3party.csp_delays.items()
                                  if k[1] == target_file and k[0].datacenter != k[1].datacenter}
            if testing_mode:
                frontend_in_same_datacenter = [fe for fe in cdgeb_utils_3party.frontend_servers
                                               if fe.datacenter == cdgeb_utils_3party.solutions[target_file]][0]
                delays_from_server.pop(frontend_in_same_datacenter)

            # Geolocation
            estimated_location = csp_geolocator.geolocate_target(delays_from_server)

            closest_datacenter = cdgeb_utils_3party.position_correction(estimated_location)

        else:
            print("[ERROR] Invalid method:", method)
            return

        # Make target-specific map file
        map_single_target = MapBuilder(f'{target_file.name}_estimated', cdgeb_utils_3party.probe_clients,
                                       cdgeb_utils_3party.datacenters)
        map_single_target.add_datacenter()
        map_single_target.add_point(estimated_location, f'estimated-location-of-{target_file.name}')

        true_file_datacenter = cdgeb_utils_3party.solutions[target_file] \
            if testing_mode else None
        true_file_coordinates = true_file_datacenter.coordinates \
            if testing_mode else None

        if testing_mode:
            map_single_target.add_circle(estimated_location,
                                         haversine(estimated_location, true_file_coordinates))
            map_single_target.add_dashed_line(estimated_location, true_file_coordinates)

        map_single_target.add_line(estimated_location, closest_datacenter.coordinates)
        map_single_target.save_map(output_dir)

        if testing_mode:
            # Calculate errors
            geolocation_error = haversine(estimated_location, true_file_coordinates)
            closest_error = haversine(closest_datacenter.coordinates, true_file_coordinates)

            errors.append((geolocation_error, closest_error))
            table.add_row(target_file.name, true_file_datacenter.name,
                          str(round(geolocation_error, 2)), str(closest_datacenter.name == true_file_datacenter.name),
                          str(round(closest_error, 2))
                          )

            map_all_targets.add_point(estimated_location, f'estimated-location-of-{target_file.name}',
                                      color="green" if closest_datacenter.name == true_file_datacenter.name else "red")
        else:
            table.add_row(target_file.name, closest_datacenter.name)

            map_all_targets.add_point(estimated_location, f'estimated-location-of-{target_file.name}',
                                      color="green")
            map_all_targets.add_dashed_line(estimated_location, closest_datacenter.coordinates)

    # Print the table
    console = Console()
    console.print(table)
    output_table_path = os.path.join(output_dir, 'table.pkl')
    # with open(output_table_path, 'wb') as f:
    #     pickle.dump(table, f)
    # with open(output_table_path, 'rb') as f:
    #     test_table = pickle.load(f)
    if testing_mode:
        final_mean_error = np.mean([err[1] for err in errors])
        final_max_error = np.max([err[1] for err in errors])
        final_rmse_error = np.sqrt(np.mean(np.square([err[1] for err in errors])))
        total_successes = len([err[1] for err in errors if err[1] == 0])
        total_attempts = len(errors)
        print("Final-Geolocation Mean Error:\t", round(final_mean_error, 2), "\t[km]")
        print("Final-Geolocation Max Error:\t", round(final_max_error, 2), "\t[km]")
        print("Final-Geolocation RMSE Error:\t", round(final_rmse_error, 2), "\t[km]")
        print(f"Success rate:\t\t\t{total_successes}/{total_attempts} ({100 * total_successes / total_attempts:.2f}%)")
        print()

        multilateration_mean_error = np.mean([err[0] for err in errors])
        multilateration_max_error = np.max([err[0] for err in errors])
        multilateration_rmse_error = np.sqrt(np.mean(np.square([err[0] for err in errors])))
        print("Multilateration Mean Error:\t", round(multilateration_mean_error, 2), "\t[km]")
        print("Multilateration Max Error:\t", round(multilateration_max_error, 2), "\t[km]")
        print("Multilateration RMSE Error:\t", round(multilateration_rmse_error, 2), "\t[km]")
        print()
    # print(
    #     f'The table is {"" if are_tables_equal(test_table, table) else "not"}similar to the original table before the change!!')

    # Save the map
    map_all_targets.save_map(output_dir)


def geolocation_main(input_dir, output_dir, method):
    testing_mode = os.path.isfile(os.path.join(input_dir, SOLUTION_DATA_FILE))

    cdgeb_utils_1party, cdgeb_utils_3party = parse_input_files(input_dir, testing_mode)

    if not validate_input_files(cdgeb_utils_1party, cdgeb_utils_3party, method, testing_mode):
        return

    csp_rates = learn_from_data(cdgeb_utils_1party, cdgeb_utils_3party, method, testing_mode)

    geolocate_from_data(output_dir, cdgeb_utils_1party, cdgeb_utils_3party, method, testing_mode)


def main(input_dir, output_dir=None, method=None):
    if not output_dir:
        output_dir = os.path.join(input_dir, 'out')
    if not check_files_exist(input_dir):
        # Already logged inside
        return

    # Create output directory if not exist
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    geolocation_main(input_dir, output_dir, method)


if __name__ == '__main__':
    print(os.getcwd())
    if len(sys.argv) > 1:
        input_dir = sys.argv[1]
    else:
        # Run from src. (python -m CDGeB1.main)
        input_dir = 'Datasets/DS-B1/'

    if len(sys.argv) > 2:
        output_dir = sys.argv[2]
    else:
        output_dir = None  # Use default

    main(input_dir, output_dir, METHOD_OPTIMIZATION)
