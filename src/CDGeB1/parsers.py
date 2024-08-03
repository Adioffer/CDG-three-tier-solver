import os
import csv
from statistics import mean, median

from CDGeB1.data_classes import *

__all__ = ['check_files_exist', 'parse_datacenters', 'parse_servers_1party', 'parse_servers_3party',
           'parse_measurements_1party', 'parse_measurements_3party', 'parse_solution', ]

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
        print("Missing file", DATACENTERS_FILE)
        return False
    if not os.path.isfile(os.path.join(input_dir, MEASUREMENT_FILE_3PARTY)):
        print("Missing file", MEASUREMENT_FILE_3PARTY)
        return False
    if not os.path.isfile(os.path.join(input_dir, SERVERS_DATA_FILE_3PARTY)):
        print("Missing file", SERVERS_DATA_FILE_3PARTY)
        return False
    return True


def parse_datacenters(input_dir) -> tuple[list[DataCenter], list[DataCenter]]:
    datacenters = list()
    possible_file_datacenters = list()

    with open(os.path.join(input_dir, DATACENTERS_FILE), 'r') as f:
        csv_reader = csv.reader(f, delimiter=',')
        for row in csv_reader:
            row = list(filter(None, row))  # Remove empty strings
            if len(row) != 4 and len(row) != 5:
                print(f"Skipping invalid row in file {DATACENTERS_FILE}: {row}")
                continue

            if len(row) == 5 and row[4] != 'learn_only':
                print(f"Skipping invalid row in file {DATACENTERS_FILE}: {row}")
                continue

            name, lat, lon, continent = row[:4]
            datacenter = DataCenter(name, (float(lat), float(lon)), Continent(continent))
            datacenters.append(datacenter)

            if len(row) == 5 and row[4] == 'learn_only':
                print("[DEBUG] learn_only datacenter:", name)
                pass
            else:
                print("[DEBUG] Possible target datacenter:", name)
                possible_file_datacenters.append(datacenter)

    return datacenters, possible_file_datacenters


def parse_servers_1party(input_dir, datacenters: list[DataCenter]):
    probe_clients = list()
    frontend_servers = list()
    data_files = list()

    with open(os.path.join(input_dir, SERVERS_DATA_FILE_1PARTY), 'r') as f:
        csv_reader = csv.reader(f, delimiter=',')
        for row in csv_reader:
            row = list(filter(None, row))  # Remove empty strings
            if len(row) == 0:
                # Skip empty lines
                continue
            if row[0] == 'probe' and len(row) == 5:
                name, lat, lon, continent = row[1:5]
                probe_clients.append(ProbeClient(name, (float(lat), float(lon)), Continent(continent)))
            elif row[0] == 'frontend' and len(row) == 3:
                name, datacenter_name = row[1:3]
                datacenter = [dc for dc in datacenters if dc.name == datacenter_name][0]
                frontend_servers.append(FrontEnd(name, datacenter))
            elif row[0] == 'file' and len(row) == 3:
                name, datacenter_name = row[1:3]
                datacenter = [dc for dc in datacenters if dc.name == datacenter_name][0]
                data_files.append(DataFile(name, datacenter))
            else:
                print("[WARNING] Skipping invalid row in file", SERVERS_DATA_FILE_1PARTY, ":", row)

    return probe_clients, frontend_servers, data_files


def parse_servers_3party(input_dir, datacenters: list[DataCenter]):
    probe_clients = list()
    frontend_servers = list()
    data_files = list()

    with open(os.path.join(input_dir, SERVERS_DATA_FILE_3PARTY), 'r') as f:
        csv_reader = csv.reader(f, delimiter=',')
        for row in csv_reader:
            row = list(filter(None, row))  # Remove empty strings
            if len(row) == 0:
                # Skip empty lines
                continue
            if row[0] == 'probe' and len(row) == 5:
                name, lat, lon, continent = row[1:5]
                probe_clients.append(ProbeClient(name, (float(lat), float(lon)), Continent(continent)))
            elif row[0] == 'frontend' and len(row) == 3:
                name, datacenter_name = row[1:3]
                datacenter = [dc for dc in datacenters if dc.name == datacenter_name][0]
                frontend_servers.append(FrontEnd(name, datacenter))
            elif row[0] == 'file' and len(row) == 2:
                name = row[1]
                data_files.append(DataFile(name))
            else:
                print("[WARNING] Skipping invalid row in file", SERVERS_DATA_FILE_3PARTY, ":", row)

    return probe_clients, frontend_servers, data_files


def aggregate_measurements(measurements):
    # return min(measurements)
    # return mean(measurements)
    # return median(measurements)
    return mean(sorted(measurements)[3:-3])


def parse_measurements(input_dir, measurement_file, probe_clients, frontend_servers, data_files):
    measurements = dict()
    with open(os.path.join(input_dir, measurement_file), 'r') as f:
        csv_reader = csv.reader(f, delimiter=',')
        for row in csv_reader:
            row = list(filter(None, row))  # Remove empty strings
            if len(row) < MEASUREMENT_FILE_ENTRY_LENGTH:
                print(f"Skipping incomplete row in file {measurement_file}: {row}")
                continue
            probe, frontend, file = row[:3]
            rtts = [float(x) for x in row[3:24]]
            measurements[(probe, frontend, file)] = aggregate_measurements(rtts)

    probes_names = set([key[MEASUREMENT_PROBES] for key in measurements])
    frontends_names = set([key[MEASUREMENT_FRONTENDS] for key in measurements])
    files_names = set([key[MEASUREMENT_FILES] for key in measurements])

    # Check for common elements
    if len(probes_names.intersection(frontends_names)) > 0:
        print("[ERROR] Probes and frontends have common elements")
        return False
    if len(probes_names.intersection(files_names)) > 0:
        print("[ERROR] Probes and files have common elements")
        return False
    if len(frontends_names.intersection(files_names)) > 0:
        print("[ERROR] Frontends and files have common elements")
        return False

    # Validate inputs are matching
    if not all(any(probe.name == probe_name for probe in probe_clients) for probe_name in probes_names):
        print("[ERROR] Some probes are not in the servers list")
        return False
    if not all(
            any(frontend.name == frontend_name for frontend in frontend_servers) for frontend_name in frontends_names):
        print("[ERROR] Some frontends are not in the servers list")
        return False
    if not all(any(file.name == file_name for file in data_files) for file_name in files_names):
        print("[ERROR] Some files are not in the servers list")
        return False

    return measurements


def parse_measurements_1party(input_dir, probe_clients, frontend_servers, data_files):
    return parse_measurements(input_dir, MEASUREMENT_FILE_1PARTY, probe_clients, frontend_servers, data_files)


def parse_measurements_3party(input_dir, probe_clients, frontend_servers, data_files):
    return parse_measurements(input_dir, MEASUREMENT_FILE_3PARTY, probe_clients, frontend_servers, data_files)


def parse_solution(input_dir, datacenters, data_files):
    file_datacenter_mapping = dict()
    with open(os.path.join(input_dir, SOLUTION_DATA_FILE), 'r') as f:
        reader = csv.reader(f, delimiter=',')
        for row in reader:
            row = list(filter(None, row))  # Remove empty strings
            if len(row) == SOLUTION_FILE_ENTRY_LENGTH:
                file_name, datacenter_name = row[:2]
                file = [file for file in data_files if file.name == file_name][0]
                datacenter = [dc for dc in datacenters if dc.name == datacenter_name][0]
                file_datacenter_mapping[file] = datacenter
            else:
                print(f"Skipping incomplete row in file {SOLUTION_DATA_FILE}: {row}")

    return file_datacenter_mapping
