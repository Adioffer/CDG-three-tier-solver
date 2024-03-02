#!/bin/bash

command="python3.11 main.py"

# Initialize total time
totalTime=0

# Number of executions
executions=10

for i in $(seq 1 $executions); do
  # Use the `time` command to measure execution time. Adjust `your_command_here` as needed.
  # The `time` format outputs only the real time in seconds with decimals.
  execTime=$( { time $command 2>&1 >/dev/null; } 2>&1 | awk '/^real/{print $2}' )
  
  # Convert time to seconds if it's not already. This depends on your `time` output format.
  # Assuming format is 'm's'ss.mmm', e.g., 0m1.234s for 1.234 seconds. Adjust parsing if needed.
  seconds=$(echo $execTime | awk -F'[ms]' '{print ($1 * 60) + $2}')
  
  # Add to total time
  totalTime=$(echo "$totalTime + $seconds" | bc)
done

# Calculate average time
averageTime=$(echo "scale=3; $totalTime / $executions" | bc)

# Print average time
echo "Average execution time: $averageTime seconds"
