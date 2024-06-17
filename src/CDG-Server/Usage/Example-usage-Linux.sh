#!/bin/bash

# Declare constants (change these as needed)
DATASET="BGU" # BGU, Fujitsu-1, Fujitsu-2
REQUESTED_FILE_NAME="results.txt" # "results.txt", "map_all_targets.html", "map_cdgeb-file-01_estimated.html", ...

# Paths to the input files
measurements="./$DATASET/measurements.csv"
servers="./$DATASET/servers.csv"
solution="./$DATASET/solution.csv"

# Create output directory if it doesn't exist
mkdir -p output

# First POST request
curl -X POST -F "measurements=@$measurements" -F "servers=@$servers" -F "solution=@$solution" https://cdgeo.net/rest --output output/output.json

# Second GET request
jq_query=".Assets.\"$REQUESTED_FILE_NAME\""
curl -X GET $(cat output/output.json | jq -r $jq_query) --output "output/$REQUESTED_FILE_NAME"
