# powershell -ExecutionPolicy Bypass -File .\misc\execution_time.ps1

$command = & C:/Users/Adi/AppData/Local/Programs/Python/Python311/python.exe "c:/Users/Adi/Desktop/Thesis/CDGeB-1/Solving Methods/three-tier-solver/src/CDGeB1/main.py"


# Initialize an array to hold execution times
$executionTimes = @()

# Loop 10 times to execute the command and measure the time taken
for ($i = 0; $i -lt 10; $i++) {
    # Measure the time taken by the command and add it to the array
    $executionTime = (Measure-Command { $command }).TotalSeconds
    $executionTimes += $executionTime
}

# Calculate the average execution time
$averageTime = ($executionTimes | Measure-Object -Average).Average

# Output the average execution time
Write-Output "Average Execution Time (10 Iterations): $averageTime seconds"