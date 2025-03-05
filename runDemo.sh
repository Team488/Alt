#!/bin/bash

# Run the Java JAR file
java -jar src/assets/XTABLES.jar&

cd src
# Run the reef/object tracking agent
python3 competitionDemo.py &

# Run the central/pathplanner agent
python3 pathPlanner.py &

# Run the reef visualizer
python3 runReefVisualizer.py &

# Wait for all background processes to finish
wait
