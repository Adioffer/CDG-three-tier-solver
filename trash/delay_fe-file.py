"""
TODO Add documentation
TODO fix
"""

from statistics import mean
from common import cdgeb_probes, cdgeb_frontends, cdgeb_files
from common import probeId2Name, frontendId2Name, fileId2Name
from common import closest_probe_to_fe, true_fe_for_file, true_file_for_fe

Input_file = 'Measurements\\150823\\full_dataset.csv'
Output_file = 'out\\out_fe-file_rtts_TMP.csv'

# Build database of all measurements, with the minimum value
measurements = dict()
with open(Input_file, 'r') as f:
	for line in f.readlines():
		probe, frontend, file = line.split(',')[0:3]
		measurements[(probe, frontend, file)] = min([float(x.replace('\n','')) for x in line.split(',')[3:]])

# Find the file that matches every front-end server
best_file_for_fe = dict()
for frontend in cdgeb_frontends:
    closest_file = min(measurements.items(),
        # pair = (key=(probe_name,frontend_name,filename), value=min_rtt)
        key=lambda pair: pair[1] if \
            # front-end == frontent
            pair[0][1] == frontend and \
            # probe = closest to frontend
            pair[0][0] == closest_probe_to_fe[frontend]
            else float('inf'))[0][2]
    best_file_for_fe[frontend] = closest_file

print("Frontend-File mapping:")
for frontend in best_file_for_fe:
    print(frontend, ":", best_file_for_fe[frontend],
          "[V]" if best_file_for_fe[frontend] == true_file_for_fe[frontend] else "[{true_file_for_fe[frontend]}]")


# Ad-hoc: fix "closest_probe_to_fe" according to is_closer_better results
# closest_probe_to_fe[frontendId2Name(1)] = probeId2Name(1)
# closest_probe_to_fe[frontendId2Name(7)] = probeId2Name(1)
# closest_probe_to_fe[frontendId2Name(13)] = probeId2Name(13)


# Compute the round-trip times of the second hop (front-end to file)
rtts_scnd_tier = dict()
for frontend in cdgeb_frontends:
    closest_file = best_file_for_fe[frontend]
    closest_probe = closest_probe_to_fe[frontend]
    
    for filename in cdgeb_files:
        rtts_scnd_tier[(frontend, filename)] = \
            measurements[(closest_probe, frontend, filename)] - \
            measurements[(closest_probe, frontend, closest_file)]

# Create a CSV file and write the data
import csv
with open(Output_file, 'w', newline='') as csvfile:
    csvwriter = csv.writer(csvfile)

    # Write the header row
    csvwriter.writerow([''] + cdgeb_files)

    # Write the data rows
    for frontend in cdgeb_frontends:
        row_data = [frontend] + [round(rtts_scnd_tier[(frontend, filename)], 6) for filename in cdgeb_files]
        csvwriter.writerow(row_data)
