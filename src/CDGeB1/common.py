from enum import StrEnum, auto

Distances_csv = 'Measurements\\150823\\out_aws-aws_distances.csv'
Aws_delays_csv = 'Measurements\\150823\\out_fe-file_rtts.csv'
Full_dataset_path = 'Measurements\\150823\\full_dataset.csv'

__all__ = [
    'probeId2Name', 'frontendId2Name', 'fileId2Name',
    'cdgeb_probes', 'cdgeb_frontends', 'cdgeb_files',
    'frontend_locations',
    'closest_probe_to_fe',
    'real_fe_for_file', 'real_file_for_fe',
    'aws_distances', 'aws_delays',

]

# Converts 1 to 'cdgeb-probe-01'
def probeId2Name(probe_id: int) -> str:
    return 'cdgeb-probe-' + str(probe_id).zfill(2)

def frontendId2Name(frontend_id: int) -> str:
    return 'cdgeb-server-' + str(frontend_id).zfill(2)

def fileId2Name(file_id: int) -> str:
    return 'cdgeb-file-' + str(file_id).zfill(2)

# Builds list of ['cdgeb-probe-01', 'cdgeb-probe-02', ...]
cdgeb_probes = [probeId2Name(probe_id) for probe_id in range(1,14+1)]
cdgeb_frontends = [frontendId2Name(frontend_id) for frontend_id in range(1,17+1)]
cdgeb_files = [fileId2Name(file_id) for file_id in range(1,17+1)]

# Real known locations of probe clients
probe_locations = {
    'cdgeb-probe-01': (45.5075, -73.5887),
    'cdgeb-probe-02': (43.6547, -79.3623),
    'cdgeb-probe-03': (-23.5335, -46.6359),
    'cdgeb-probe-04': (45.5999, -121.1871),
    'cdgeb-probe-05': (34.0544, -118.2441),
    'cdgeb-probe-06': (52.2296, 21.0067),
    'cdgeb-probe-07': (61.0636, 28.189),
    'cdgeb-probe-08': (40.4163, -3.6934),
    'cdgeb-probe-09': (25.2952, 51.5321),
    'cdgeb-probe-10': (32.0803, 34.7805),
    'cdgeb-probe-11': (25.0504, 121.5324),
    'cdgeb-probe-12': (22.2842, 114.1759),
    'cdgeb-probe-13': (35.6893, 139.6899),
    'cdgeb-probe-14': (34.6946, 135.5021),
}

# Real known locations of front-end servers
frontend_locations = {
    "cdgeb-server-01": (39.0469, -77.4903),
    "cdgeb-server-02": (51.5088, -0.093),
    "cdgeb-server-03": (-23.5335, -46.6359),
    "cdgeb-server-04": (35.6893, 139.6899),
    "cdgeb-server-05": (1.2929, 103.8547),
    "cdgeb-server-06": (45.5075, -73.5887),
    "cdgeb-server-07": (39.9587, -82.9987),
    "cdgeb-server-08": (37.1835, -121.7714),
    "cdgeb-server-09": (45.8234, -119.7257),
    "cdgeb-server-10": (19.0748, 72.8856),
    "cdgeb-server-11": (34.6946, 135.5021),
    "cdgeb-server-12": (37.4585, 126.7015),
    "cdgeb-server-13": (-33.8715, 151.2006),
    "cdgeb-server-14": (50.1188, 8.6843),
    "cdgeb-server-15": (53.3379, -6.2591),
    "cdgeb-server-16": (48.4323, 2.4075),
    "cdgeb-server-17": (59.3287, 18.0717),    
}

class Continent(StrEnum):
    AS = "Asia",            # Asia
    EU = "Europe",          # Europe
    #AF = auto(),            # Africa
    AMN = "N. America",     # North America
    AMS = "S. America",     # South America
    AU = "Australia",       # Australia (Oceania)

frontend_continents = {
    "cdgeb-server-01": Continent.AMN,
    "cdgeb-server-02": Continent.EU,
    "cdgeb-server-03": Continent.AMS,
    "cdgeb-server-04": Continent.AS,
    "cdgeb-server-05": Continent.AS,
    "cdgeb-server-06": Continent.AMN,
    "cdgeb-server-07": Continent.AMN,
    "cdgeb-server-08": Continent.AMN,
    "cdgeb-server-09": Continent.AMN,
    "cdgeb-server-10": Continent.AS,
    "cdgeb-server-11": Continent.AS,
    "cdgeb-server-12": Continent.AS,
    "cdgeb-server-13": Continent.AU,
    "cdgeb-server-14": Continent.EU,
    "cdgeb-server-15": Continent.EU,
    "cdgeb-server-16": Continent.EU,
    "cdgeb-server-17": Continent.EU,
}

aws_general_rate = 122327.002

aws_rates = {(Continent.AS, Continent.AS): 102356.44, (Continent.AS, Continent.EU): 93725.71, (Continent.AS, Continent.AMN): 143517.57, (Continent.AS, Continent.AMS): 122182.88, (Continent.AS, Continent.AU): 130212.12, (Continent.EU, Continent.AS): 92885.87, (Continent.EU, Continent.EU): 93627.7, (Continent.EU, Continent.AMN): 124836.04, (Continent.EU, Continent.AMS): 98100.46, (Continent.EU, Continent.AU): 124436.58, (Continent.AMN, Continent.AS): 141513.06, (Continent.AMN, Continent.EU): 124629.63, (Continent.AMN, Continent.AMN): 115453.69, (Continent.AMN, Continent.AMS): 123053.64, (Continent.AMN, Continent.AU): 164926.93, (Continent.AMS, Continent.AS): 125062.16, (Continent.AMS, Continent.EU): 103199.75, (Continent.AMS, Continent.AMN): 131991.45, (Continent.AMS, Continent.AMS): float('inf'), (Continent.AMS, Continent.AU): 86855.66, (Continent.AU, Continent.AS): 131804.0, (Continent.AU, Continent.EU): 125483.25, (Continent.AU, Continent.AMN): 167488.0, (Continent.AU, Continent.AMS): 85826.62, (Continent.AU, Continent.AU): float('inf')}

# The closest probe to each front-end server
# (Data has been computed from advance)
closest_probe_to_fe = {
    'cdgeb-server-01': 'cdgeb-probe-02',
    'cdgeb-server-02': 'cdgeb-probe-08',
    'cdgeb-server-03': 'cdgeb-probe-03',
    'cdgeb-server-04': 'cdgeb-probe-13',
    'cdgeb-server-05': 'cdgeb-probe-12',
    'cdgeb-server-06': 'cdgeb-probe-01',
    'cdgeb-server-07': 'cdgeb-probe-02',
    'cdgeb-server-08': 'cdgeb-probe-05',
    'cdgeb-server-09': 'cdgeb-probe-04',
    'cdgeb-server-10': 'cdgeb-probe-09',
    'cdgeb-server-11': 'cdgeb-probe-14',
    'cdgeb-server-12': 'cdgeb-probe-14',
    'cdgeb-server-13': 'cdgeb-probe-11',
    'cdgeb-server-14': 'cdgeb-probe-06',
    'cdgeb-server-15': 'cdgeb-probe-08',
    'cdgeb-server-16': 'cdgeb-probe-08',
    'cdgeb-server-17': 'cdgeb-probe-07',
}

# The real mapping between files and front-end servers
real_fe_for_file = {
    'cdgeb-file-01': 'cdgeb-server-04',
    'cdgeb-file-02': 'cdgeb-server-14',
    'cdgeb-file-03': 'cdgeb-server-12',
    'cdgeb-file-04': 'cdgeb-server-17',
    'cdgeb-file-05': 'cdgeb-server-07',
    'cdgeb-file-06': 'cdgeb-server-08',
    'cdgeb-file-07': 'cdgeb-server-06',
    'cdgeb-file-08': 'cdgeb-server-01',
    'cdgeb-file-09': 'cdgeb-server-10',
    'cdgeb-file-10': 'cdgeb-server-02',
    'cdgeb-file-11': 'cdgeb-server-15',
    'cdgeb-file-12': 'cdgeb-server-09',
    'cdgeb-file-13': 'cdgeb-server-05',
    'cdgeb-file-14': 'cdgeb-server-16',
    'cdgeb-file-15': 'cdgeb-server-13',
    'cdgeb-file-16': 'cdgeb-server-03',
    'cdgeb-file-17': 'cdgeb-server-11',
}
real_file_for_fe = {v:k for k,v in real_fe_for_file.items()}

def _serialize_distances_csv():
    with open(Distances_csv, 'r') as f:
        lines = f.read().splitlines()

    distances = dict() # Elements: {('cdgeb-server-X', 'cdgeb-file-Y'): delay_s}
    
    for line_number, line in enumerate(lines):
        if line_number == 0:
             # First line is header
            continue

        frontend = frontendId2Name(line_number)
        for column_number, dist in enumerate(line.split(',')):
            if column_number == 0:
                 # First column is header - ignore
                continue

            # This is because: file-X is not placed on the X'th datacenter,
            # rather file-Y, where Y<->X is defined by real_file_for_fe
            tmp_frontend = frontendId2Name(column_number)
            filename = real_file_for_fe[tmp_frontend]
            distances[(frontend, filename)] = float(dist)

    return distances

def _serialize_aws_delays():
    with open(Aws_delays_csv, 'r') as f:
        lines = f.read().splitlines()

    delays = dict() # Elements: {('cdgeb-server-X', 'cdgeb-file-Y'): delay_s}
    
    for line_number, line in enumerate(lines):
        if line_number == 0:
             # First line is header
            continue

        frontend_name = frontendId2Name(line_number)
        for column_number, delay in enumerate(line.split(',')):
            if column_number == 0:
                 # First column is header
                continue

            filename = fileId2Name(column_number)
            delays[(frontend_name, filename)] = float(delay) / 2 # /2 -> single direction

    return delays

# aws_distances =  {('cdgeb-server-X', 'cdgeb-file-Y'), distance_km}
aws_distances = _serialize_distances_csv()
# aws_distances = {('cdgeb-server-X', 'cdgeb-file-Y'), delay_s}
aws_delays = _serialize_aws_delays()
