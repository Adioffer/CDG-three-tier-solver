"""
This code checks whether the closest probe to the frontend is the "best" probe for this frontend,
in terms of which probe received the most measurements with lowest time measurements to all 17 files.
Code output is provided below.
"""

from common import cdgeb_probes, cdgeb_frontends, cdgeb_files
from common import closest_probe_to_fe
from common import Full_dataset_path

# Build database of all measurements, with the minimum value
measurements = dict()
with open(Full_dataset_path, 'r') as f:
	for line in f.readlines():
		probe, frontend, file = line.split(',')[0:3]
		measurements[(probe, frontend, file)] = min([float(x.replace('\n','')) for x in line.split(',')[3:]])

# Find the file that matches every front-end server
best_probe_for_fe = dict()
for frontend in cdgeb_frontends:
    best4fe = dict()
    for filename in cdgeb_files:
        best_probe = min(measurements.items(),
            key = lambda pair: pair[1] if \
            pair[0][1] == frontend and \
            pair[0][2] == filename \
            else float('inf'))[0][0]
        best4fe[best_probe] = best4fe[best_probe] + 1 if best_probe in best4fe \
            else 1
    print(frontend, ": ")
    print(best4fe)
    best_probe_for_fe[frontend] = max(best4fe, key=best4fe.get)
    
print()
for frontend in cdgeb_frontends:
    print(frontend, ":", best_probe_for_fe[frontend], closest_probe_to_fe[frontend], \
        "[]" if best_probe_for_fe[frontend] == closest_probe_to_fe[frontend] else "[X]")

"""
Output: (for 15.08.2023 measurements)
cdgeb-server-01 : cdgeb-probe-01 cdgeb-probe-02 [X]
cdgeb-server-02 : cdgeb-probe-08 cdgeb-probe-08 []
cdgeb-server-03 : cdgeb-probe-03 cdgeb-probe-03 []
cdgeb-server-04 : cdgeb-probe-13 cdgeb-probe-13 []
cdgeb-server-05 : cdgeb-probe-12 cdgeb-probe-12 []
cdgeb-server-06 : cdgeb-probe-01 cdgeb-probe-01 []
cdgeb-server-07 : cdgeb-probe-01 cdgeb-probe-02 [X]
cdgeb-server-08 : cdgeb-probe-05 cdgeb-probe-05 []
cdgeb-server-09 : cdgeb-probe-04 cdgeb-probe-04 []
cdgeb-server-10 : cdgeb-probe-09 cdgeb-probe-09 []
cdgeb-server-11 : cdgeb-probe-14 cdgeb-probe-14 []
cdgeb-server-12 : cdgeb-probe-14 cdgeb-probe-14 []
cdgeb-server-13 : cdgeb-probe-13 cdgeb-probe-11 [X]
cdgeb-server-14 : cdgeb-probe-06 cdgeb-probe-06 []
cdgeb-server-15 : cdgeb-probe-08 cdgeb-probe-08 []
cdgeb-server-16 : cdgeb-probe-08 cdgeb-probe-08 []
cdgeb-server-17 : cdgeb-probe-07 cdgeb-probe-07 []
"""
