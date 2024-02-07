"""
TODO Add documentation
TODO fix
"""

from statistics import mean
from common import cdgeb_probes, cdgeb_frontends, cdgeb_files
from common import probeId2Name, frontendId2Name, fileId2Name
from common import closest_probe_to_fe, real_fe_for_file

Input_file = 'full_dataset.csv'
Output_file = 'delay_fe-file.csv'

# Build database of all measurements, with the minimum value
measurements = dict()
with open(Input_file, 'r') as f:
	for line in f.readlines():
		probe, frontend, file = line.split(',')[0:3]
		measurements[(probe, frontend, file)] = min([float(x.replace('\n','')) for x in line.split(',')[3:]])

# Find the file that matches every front-end server
best_file_for_fe = dict()
for frontend in cdgeb_frontends:
    method = 2
    
    match(method):
        case 1:
            closest_file = min(measurements.items(),
                # pair = (key=(probe_name,frontend_name,filename), value=min_rtt)
                key=lambda pair: pair[1] if \
                    # probe_name == probename
                    pair[0][1] == frontend \
                    else float('inf'))[0][2]
                    
        case 2:
            closest_file = min(measurements.items(),
                # pair = (key=(probe_name,frontend_name,filename), value=min_rtt)
                key=lambda pair: pair[1] if \
                    # front-end == frontent
                    pair[0][1] == frontend and \
                    # probe = closest to frontend
                    pair[0][0] == closest_probe_to_fe[frontend]
                    else float('inf'))[0][2]
    
    if closest_file in best_file_for_fe.values():
        print(f"{closest_file} matches both {frontend} and {best_fe_for_file[closest_file]}. aborting.")
        exit()
    best_file_for_fe[frontend] = closest_file

print(best_file_for_fe)
exit(0)


# Print the results, compare with known results
print("filename\texpected\tcomputed")
[print(filename, a:=real_fe_for_file[filename], b:=best_fe_for_file[filename], '[V]' if a == b else '[]', sep='\t') for filename in cdgeb_files]

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
        row_data = [frontend] + [rtts_scnd_tier[(frontend, filename)] for filename in cdgeb_files]
        csvwriter.writerow(row_data)
