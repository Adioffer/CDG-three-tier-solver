


# # DS-B1-V1
# Input_file = 'DS-B1/measurements.csv'
# Output_file = 'DS-B1-V1/sub_measurements.csv'
# files = ["cdgeb-file-01", "cdgeb-file-02", "cdgeb-file-03", "cdgeb-file-04", "cdgeb-file-05"]
# frontends = ["cdgeb-server-04", "cdgeb-server-14", "cdgeb-server-12", "cdgeb-server-17", "cdgeb-server-07"]

# DS-B1-V2
Input_file = 'DS-B1/measurements.csv'
Output_file = 'DS-B1-V2/sub_measurements.csv'
files = ["cdgeb-file-01", "cdgeb-file-02", "cdgeb-file-03", "cdgeb-file-04", "cdgeb-file-05",
         "cdgeb-file-06", "cdgeb-file-07", "cdgeb-file-16", "cdgeb-file-13", "cdgeb-file-11"]
frontends = ["cdgeb-server-04", "cdgeb-server-14", "cdgeb-server-12", "cdgeb-server-17", "cdgeb-server-07",
             "cdgeb-server-08", "cdgeb-server-06", "cdgeb-server-03", "cdgeb-server-05", "cdgeb-server-15"]


measurements = list()
with open(Input_file, 'r') as f:
    measurements = f.readlines()

sub_measurements = [line for line in measurements \
					if line.split(',')[1] in frontends \
					and line.split(',')[2] in files]

with open(Output_file, 'w') as f:
    f.writelines(sub_measurements)
		
