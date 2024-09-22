# Declare constants (change these as needed)
$DATASET = "BGU" # BGU, Fujitsu-1, Fujitsu-2
$REQUESTED_FILE_NAME = "results.txt" # "results.txt", "map_all_targets.html", "map_cdgeb-file-01_estimated.html", ...

# Paths to the input files
$measurements = "./$DATASET/measurements.csv"
$servers = "./$DATASET/servers.csv"
$solution = "./$DATASET/solution.csv"

# Create output directory if it doesn't exist
if (!(Test-Path -Path "output")) {
    New-Item -ItemType Directory -Path "output"
}

# First POST request
$uri = "https://127.0.0.1:5000/rest"
cmd /c curl $uri -X POST -H "Content-Type: multipart/form-data" -F "measurements=@$measurements" -F "servers=@$servers" -F "solution=@$solution" -o "output/output.json"

# Second GET request
$outputJson = Get-Content -Path "output/output.json" | ConvertFrom-Json
$fileUrl = $outputJson.Assets.$REQUESTED_FILE_NAME
Invoke-RestMethod -Method Get -Uri "$fileUrl" -OutFile "output/$REQUESTED_FILE_NAME"
