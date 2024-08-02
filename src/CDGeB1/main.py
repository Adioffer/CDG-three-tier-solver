import os
import sys
import csv
from statistics import mean, median
import numpy as np
from rich.console import Console
from rich.table import Table
from CDGeB1.GeolocationUtils import GeolocationUtils
from CDGeB1.GeolocationCSP import Geolocation
from CDGeB1.common import Continent
from CDGeB1.plot_map import MapBuilder
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

def check_files_exist(input_dir):
    filepath = os.path.join(input_dir, MEASUREMENT_FILE_1PARTY)
    if not os.path.isfile(filepath):
        print("Missing file", MEASUREMENT_FILE_1PARTY)
        return False
    if not os.path.isfile(os.path.join(input_dir, SERVERS_DATA_FILE_1PARTY)):
        print("Missing file", SERVERS_DATA_FILE_1PARTY)
        return False
    if not os.path.isfile(os.path.join(input_dir, DATACENTERS_FILE)):
        return False
    if not os.path.isfile(os.path.join(input_dir, MEASUREMENT_FILE_3PARTY)):
        return False
    if not os.path.isfile(os.path.join(input_dir, SERVERS_DATA_FILE_3PARTY)):
        return False
    return True


def aggregateMeasurements(measurements):
    # return min(measurements)
    # return mean(measurements)
    # return median(measurements)
    return mean(sorted(measurements)[3:-3])


def parse_datasets_1party(input_dir):
    # Load measurements from CSV
    measurements_1party = dict()
    with open(os.path.join(input_dir, MEASUREMENT_FILE_1PARTY), 'r') as f:
        csv_reader = csv.reader(f)
        for row in csv_reader:
            if len(row) < MEASUREMENT_FILE_ENTRY_LENGTH:
                print(f"Skipping incomplete row in file {MEASUREMENT_FILE_1PARTY}: {row}")
                continue
            probe, frontend, file = row[:3]
            measurements = [float(x) for x in row[3:24]]
            measurements_1party[(probe, frontend, file)] = aggregateMeasurements(measurements)

    probes_set = set([key[MEASUREMENT_PROBES] for key in measurements_1party])
    frontends_set = set([key[MEASUREMENT_FRONTENDS] for key in measurements_1party])
    files_set = set([key[MEASUREMENT_FILES] for key in measurements_1party])

    # Check for common elements
    if len(probes_set.intersection(frontends_set)) > 0:
        print("Probes and frontends have common elements")
        return False
    if len(probes_set.intersection(files_set)) > 0:
        print("Probes and files have common elements")
        return False
    if len(frontends_set.intersection(files_set)) > 0:
        print("Frontends and files have common elements")
        return False

    # Load servers data
    server_locations = dict()
    file_datacenter_mapping = dict()
    server_datacenter_mapping = dict()
    with open(os.path.join(input_dir, SERVERS_DATA_FILE_1PARTY), 'r') as f:
        csv_reader = csv.reader(f)
        for row in csv_reader:
            if len(row) == 0:
                # Skip empty lines
                continue
            if len(row) < SERVER_FILE_FULL_ENTRY_LENGTH:
                name, datacenter = row[:2]
                if name in files_set:
                    file_datacenter_mapping[name] = datacenter
                elif name in frontends_set:
                    server_datacenter_mapping[name] = datacenter
            else:
                servername, lat, lon, continent = row[:4]
                server_locations[servername] = (float(lat), float(lon), Continent(continent))

    datacenter_locations = dict()
    possible_file_locations = dict()

    with open(os.path.join(input_dir, DATACENTERS_FILE), 'r') as f:
        csv_reader = csv.reader(f)
        for row in csv_reader:
            if len(row) < DATACENTER_FILE_ENTRY_LENGTH:
                print(f"Skipping incomplete row in file {DATACENTERS_FILE}: {row}")
                continue
            name, lat, lon, continent, only_learn = row[:5]
            datacenter_locations[name] = (float(lat), float(lon), continent)
            if only_learn and only_learn == 'learn_only':
                print("Found learn_only:", name)
                pass
            else:
                possible_file_locations[name] = (float(lat), float(lon), continent)
                print("Possible location:", name)

    # Check if all probes, frontends and files are in the servers list
    if not all(probe in server_locations for probe in probes_set):
        print("Some probes are not in the servers list")
        return False
    if not all(frontend in server_datacenter_mapping for frontend in frontends_set):
        print("Some frontends are not in the servers list")
        return False
    if not all(file in file_datacenter_mapping for file in files_set):
        print("Some files are not in the servers list")
        return False

    # Create dictionaries for locations and continents
    def sortDict(d):
        return dict(sorted(d.items(), key=lambda item: item[0]))

    def find_frontend_location(frontend):
        datacenter = server_datacenter_mapping[frontend]
        return datacenter_locations[datacenter]

    def find_file_location(file):
        datacenter = file_datacenter_mapping[file]
        return datacenter_locations[datacenter]

    probe_locations = sortDict({probe: server_locations[probe][:COORDINATES_LENGTH] for probe in probes_set})
    frontend_locations = sortDict({frontend: find_frontend_location(frontend) for frontend in frontends_set})
    frontend_continents = sortDict({frontend: find_frontend_location(frontend)[COORDINATES_LENGTH] for frontend in frontends_set})
    file_locations = sortDict({file: find_file_location(file) for file in files_set})

    cdgeb_geolocation_utils = GeolocationUtils(
        file_frontend_mapping=file_datacenter_mapping,
        probe_locations=probe_locations,
        frontend_locations=frontend_locations,
        frontend_continents=frontend_continents,
        file_locations=file_locations,
        datacenter_locations=datacenter_locations,
        possible_file_locations=possible_file_locations
    )

    return measurements_1party, probe_locations, frontend_locations, frontend_continents, \
           cdgeb_geolocation_utils


def parse_datasets_3party(input_dir, datacenter_location):
    # Load measurements from CSV
    measurements_3party = dict()
    with open(os.path.join(input_dir, MEASUREMENT_FILE_3PARTY), 'r') as f:
        csv_reader = csv.reader(f)
        for row in csv_reader:
            if len(row) < MEASUREMENT_FILE_ENTRY_LENGTH:
                print(f"Skipping incomplete row in file {DATACENTERS_FILE}: {row}")
                continue
            probe, frontend, file = row[:3]
            measurements = [float(x) for x in row[3:24]]
            measurements_3party[(probe, frontend, file)] = aggregateMeasurements(measurements)

    probes_set = set([key[MEASUREMENT_PROBES] for key in measurements_3party])
    frontends_set = set([key[MEASUREMENT_FRONTENDS] for key in measurements_3party])
    files_set = set([key[MEASUREMENT_FILES] for key in measurements_3party])
    # Load servers data
    server_locations = dict()
    server_datacenter_mapping = dict()
    with open(os.path.join(input_dir, SERVERS_DATA_FILE_3PARTY), 'r') as f:
        csv_reader = csv.reader(f)
        for row in csv_reader:
            if len(row) == 0:
                # Skip empty lines
                continue
            if len(row) < SERVER_FILE_FULL_ENTRY_LENGTH:
                name, datacenter = row[:2]
                if name in frontends_set:
                    server_datacenter_mapping[name] = datacenter
            else:
                servername, lat, lon, continent = row[:4]
                server_locations[servername] = (float(lat), float(lon), Continent(continent))

    # Check if all probes, frontends and files are in the servers list
    if not all(probe in server_locations for probe in probes_set):
        print("Some probes are not in the servers list")
        return False
    if not all(frontend in frontends_set for frontend in frontends_set):
        print("Some frontends are not in the servers list")
        return False
    if not all(file in files_set for file in files_set):
        print("Some files are not in the servers list")
        return False

    # Create dictionaries for locations and continents
    def sortDict(d):
        return dict(sorted(d.items(), key=lambda item: item[0]))

    def find_frontend_location(frontend):
        datacenter = server_datacenter_mapping[frontend]
        return datacenter_location[datacenter]

    frontend_locations = sortDict({frontend: find_frontend_location(frontend) for frontend in frontends_set})

    file_locations = None
    file_datacenter_mapping = None
    if os.path.isfile(os.path.join(input_dir, SOLUTION_DATA_FILE)):
        file_datacenter_mapping = dict()
        with open(os.path.join(input_dir, SOLUTION_DATA_FILE), 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) >= SOLUTION_FILE_ENTRY_LENGTH:
                    file, datacenter = row[:2]
                    file_datacenter_mapping[file] = datacenter
        file_locations = {file: datacenter_location[datacenter] for file, datacenter in file_datacenter_mapping.items()}

    return measurements_3party, frontend_locations, files_set, file_locations, file_datacenter_mapping


def learn_from_data(measurements_1party, cdgeb_geolocation_utils, measurements_3party, frontend_locations_3party,
                    filenames_3party):
    # Stage 1 - Compute delays within CSP

    distance_map = cdgeb_geolocation_utils.build_distance_map()
    cdgeb_geolocation_utils.csp_distances = distance_map

    closets_probe_to_frontends = cdgeb_geolocation_utils.determine_closest_probes()
    cdgeb_geolocation_utils.closets_probe_to_frontends = closets_probe_to_frontends

    closest_file_for_frontend = cdgeb_geolocation_utils.determine_closest_files(measurements_1party)
    cdgeb_geolocation_utils.closest_file_for_frontend = closest_file_for_frontend

    rtts_within_csp = cdgeb_geolocation_utils.compute_csp_delays(measurements_1party)
    csp_delays = {k: v / 2 for k, v in rtts_within_csp.items()}
    cdgeb_geolocation_utils.csp_delays = csp_delays

    csp_general_rate = cdgeb_geolocation_utils.evaluate_csp_general_rate()
    csp_rates = cdgeb_geolocation_utils.evaluate_csp_rates()

    rtts_within_csp = cdgeb_geolocation_utils.compute_csp_delays_test(measurements_1party, measurements_3party,
                                                                      frontend_locations_3party, filenames_3party)
    csp_delays = {k: v / 2 for k, v in rtts_within_csp.items()}
    cdgeb_geolocation_utils.csp_delays = csp_delays


    datacenter_frontend_mapping = {datacenter: frontend for datacenter, datacenter_loc in
                                   cdgeb_geolocation_utils.datacenter_locations.items() for frontend, frontend_loc in
                                   cdgeb_geolocation_utils.frontend_locations.items() if datacenter_loc == frontend_loc}

    # Save results
    # TODO

    # Stage 2 - Compute transmission rates within CSP


    # Print results
    GeolocationUtils.pretty_print_rates(csp_rates)
    print("Rates within CSP (All measuremenets):", csp_general_rate)
    print()

    return csp_delays, csp_general_rate, csp_rates, datacenter_frontend_mapping


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


def geolocate_from_data(cdgeb_utils,  # used for geolocation
                        # Used for building geolocation setup
                        csp_delays, csp_rates,  # used for geolocation
                        Output_dir, datacenter_frontend_mapping, filenames, file_locations, file_datacenter_mapping
                        ):
    if file_locations:
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


    # Stages 3-5 - Geolocation
    # Create map of all geolocated targets
    map_all_targets = MapBuilder("all_targets", cdgeb_utils.probe_locations, cdgeb_utils.frontend_locations)
    map_all_targets.add_datacenter()

    # Initialize a geolocator
    csp_geolocator = Geolocation(cdgeb_utils.frontend_locations, cdgeb_utils.possible_file_locations, csp_rates=csp_rates, frontend_continents=cdgeb_utils.frontend_continents)

    errors = []
    for filename in filenames:
        # Geolocate current file using measurements from other frontends
        delays_from_server = {frontend_name: csp_delays[(frontend_name, filename_d)] for (frontend_name, filename_d) in
                              csp_delays.keys() if filename_d == filename}


        if file_datacenter_mapping:
            true_datacenter = file_datacenter_mapping[filename]
            true_frontend = datacenter_frontend_mapping[true_datacenter]
            delays_from_server.pop(true_frontend)

        # Geolocation
        estimated_location = csp_geolocator.geolocate_target(delays_from_server)

        # Second-time geolocation - distance
        # tmp_frontends = list(delays_from_server.keys()) # Workaround
        # for frontend_name in tmp_frontends:
        #     if GeolocationUtils.haversine(frontend_locations[frontend_name], estimated_location) > 3000:
        #         delays_from_server.pop(frontend_name)
        # if len(delays_from_server) < 3:
        #     print(f"Skipping double-geolocation for {filename} due to lack of measurements")
        # else:
        #     estimated_location = csp_geolocator.geolocate_target(delays_from_server)

        # Second-time geolocation - k-nearest
        # tmp_frontends = list(delays_from_server.keys()) # Workaround
        # tmp_frontends.sort(key=lambda x: GeolocationUtils.haversine(frontend_locations[x], estimated_location))
        # k = 6
        # for frontend_name in tmp_frontends[k:]:
        #     delays_from_server.pop(frontend_name)
        # estimated_location = csp_geolocator.geolocate_target(delays_from_server)

        closest_datacenter = csp_geolocator.position_correction(estimated_location)

        # Make target-specific map file
        map_single_target = MapBuilder(f'{filename}_estimated', cdgeb_utils.probe_locations, cdgeb_utils.datacenter_locations)
        map_single_target.add_datacenter()
        map_single_target.add_point(estimated_location, f'estimated-location-of-{filename}')
        if file_locations:
            map_single_target.add_circle(estimated_location,
                                         GeolocationUtils.haversine(estimated_location, file_locations[filename][:COORDINATES_LENGTH]))
            map_single_target.add_dashed_line(estimated_location, file_locations[filename][:COORDINATES_LENGTH])
        map_single_target.add_line(estimated_location, cdgeb_utils.datacenter_locations[closest_datacenter][:COORDINATES_LENGTH])
        map_single_target.save_map(Output_dir)

        if file_datacenter_mapping:
            # Calculate errors
            geolocation_error = GeolocationUtils.haversine(cdgeb_utils.datacenter_locations[true_datacenter][:COORDINATES_LENGTH], estimated_location)
            closest_error = GeolocationUtils.haversine(cdgeb_utils.datacenter_locations[true_datacenter][:COORDINATES_LENGTH],
                                                       cdgeb_utils.datacenter_locations[closest_datacenter][:COORDINATES_LENGTH])

            errors.append((geolocation_error, closest_error))
            table.add_row(filename, true_datacenter,
                          str(round(geolocation_error, 2)), str(closest_datacenter == true_datacenter),
                          str(round(closest_error, 2))
                          )

            map_all_targets.add_point(estimated_location, f'estimated-location-of-{true_datacenter}',
                                      color="green" if closest_datacenter == true_datacenter else "red")
        else:
            table.add_row(filename, closest_datacenter)

    # Print the table
    console = Console()
    console.print(table)
    output_table_path = os.path.join(Output_dir, 'table.pkl')
    # with open(output_table_path, 'wb') as f:
    #     pickle.dump(table, f)
    # with open(output_table_path, 'rb') as f:
    #     test_table = pickle.load(f)
    if file_locations:
        rmse_error = np.sqrt(np.mean(np.square([err[0] for err in errors])))
        print("Geolocation Error (RMSE): ", round(rmse_error, 2), "[km]")
        rmse_error = np.sqrt(np.mean(np.square([err[1] for err in errors])))
        print("Closest Geolocation Error (RMSE): ", round(rmse_error, 2), "[km]")
        print()
    # print(
    #     f'The table is {"" if are_tables_equal(test_table, table) else "not"}similar to the original table before the change!!')

    # Save the map
    map_all_targets.save_map(Output_dir)


def geolocation_main(input_dir, output_dir):
    # extra caution is needed here ;)
    measurements_1party, probe_locations_1party, frontend_locations_1party, frontend_continents_1party, cdgeb_utils =\
        parse_datasets_1party(input_dir)

    measurements_3party, frontend_locations_3party, filenames, file_locations, file_datacenter_mapping = \
        parse_datasets_3party(input_dir, cdgeb_utils.datacenter_locations)

    csp_delays, csp_general_rate, csp_rates, datacenter_frontend_mapping = learn_from_data(measurements_1party,
                                                                                           cdgeb_utils,
                                                                                           measurements_3party,
                                                                                           frontend_locations_3party,
                                                                                           filenames)

    geolocate_from_data(cdgeb_utils, csp_delays, csp_rates, output_dir, datacenter_frontend_mapping, filenames,
                        file_locations, file_datacenter_mapping)

    # TODO: csp_rates should actually be recalculated in the geolocate_from_data function
    # TODO: (to represent the 'user' rtts and not the 'geolocator' rtts)


def main(input_dir, output_dir=None):
    if not output_dir:
        output_dir = os.path.join(input_dir, 'out')
    if not check_files_exist(input_dir):
        # Already logged inside
        return

    # Create output directory if not exist
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    geolocation_main(input_dir, output_dir)


if __name__ == '__main__':
    print(os.getcwd())
    if len(sys.argv) > 1:
        input_dir = sys.argv[1]
    else:
        # Run from src. (python -m CDGeB1.main)
        input_dir = 'Datasets/BGU-150823/'
        third_pary_dataset = os.path.join(input_dir, '3_party')
        # input_dir = 'CDGeB1\\Datasets\\Fujitsu-240216'
        # input_dir = 'CDGeB1\\Datasets\\Fujitsu-240304'

    if len(sys.argv) > 2:
        Output_dir = sys.argv[2]
    else:
        Output_dir = None  # Use default

    main(input_dir, Output_dir)
