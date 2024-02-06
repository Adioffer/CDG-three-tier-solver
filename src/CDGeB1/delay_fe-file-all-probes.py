"""
TODO Add documentation
TODO fix
"""

import matplotlib.pyplot as plt
from common import cdgeb_probes, cdgeb_frontends, cdgeb_files
from common import probeId2Name, frontendId2Name, fileId2Name

Input_file = 'full_dataset.csv'
Output_file = 'delay_fe-file.csv'


# Build database of all measurements, with the minimum value
measurements = dict()
with open(Input_file, 'r') as f:
	for line in f.readlines():
		probe, frontend, file = line.split(',')[0:3]
		measurements[(probe, frontend, file)] = min([float(x.replace('\n','')) for x in line.split(',')[3:]])

# Computed previously in delay-fe-file.py
best_file_for_fe = {'cdgeb-server-01': 'cdgeb-file-08', 'cdgeb-server-02': 'cdgeb-file-10', 'cdgeb-server-03': 'cdgeb-file-16', 'cdgeb-server-04': 'cdgeb-file-01', 'cdgeb-server-05': 'cdgeb-file-13', 'cdgeb-server-06': 'cdgeb-file-07', 'cdgeb-server-07': 'cdgeb-file-05', 'cdgeb-server-08': 'cdgeb-file-06', 'cdgeb-server-09': 'cdgeb-file-12', 'cdgeb-server-10': 'cdgeb-file-09', 'cdgeb-server-11': 'cdgeb-file-17', 'cdgeb-server-12': 'cdgeb-file-03', 'cdgeb-server-13': 'cdgeb-file-15', 'cdgeb-server-14': 'cdgeb-file-02', 'cdgeb-server-15': 'cdgeb-file-11', 'cdgeb-server-16': 'cdgeb-file-14', 'cdgeb-server-17': 'cdgeb-file-04'}

with open('aws-distances.csv', 'r') as f:
    rows = f.read().splitlines()

# This is a hack. Note that first line (rows[0]) and first col (...) are headers.
def get_distance_from(frontend, filename):
    frontend_id = int(frontend[-2:])
    file_id = int(filename[-2:])
    return rows[frontend_id].split(',')[file_id]

# Compute the round-trip times of the second hop (front-end to file)
rtts_scnd_tier = dict()
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
colors += colors
def paint_all_frontends():
    fig, ax = plt.subplots()
    for frontend, color in zip(cdgeb_frontends, colors):
        closest_file = best_file_for_fe[frontend]
        
        for probe in cdgeb_probes:
            Xs = list()
            Ys = list()
            for filename in cdgeb_files:
                Xs.append(get_distance_from(frontend, filename))
                Ys.append(measurements[(probe, frontend, filename)] - \
                    measurements[(probe, frontend, closest_file)])
            
            ax.scatter(Xs, Ys, color=color)
    plt.show()

def paint_single_frontend(fe):
    fig, ax = plt.subplots()
    # for frontend in cdgeb_frontends:
    for frontend in [common.frontendId2Name(fe)]:
        closest_file = best_file_for_fe[frontend]
        
        for probe, color in zip(cdgeb_probes, colors):
            Xs = list()
            Ys = list()
            for filename in cdgeb_files:
                Xs.append(get_distance_from(frontend, filename))
                Ys.append(measurements[(probe, frontend, filename)] - \
                    measurements[(probe, frontend, closest_file)])
            
            ax.scatter(Xs, Ys, color=color)
    plt.show()

# paint_all_frontends()
paint_single_frontend(2)