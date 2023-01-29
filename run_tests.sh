#!/bin/bash

for file in "examples/Telemetry"/*; do
    example=$(basename "$file")
    simpath="examples/Simulations/"$example
    testpath="examples/Telemetry/"$example"/telemetry.csv"
    clear; python3 main.py -s $simpath -t $testpath
done