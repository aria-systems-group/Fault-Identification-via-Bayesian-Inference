#!/bin/bash

for file in "tests/Telemetry"/*; do
    example=$(basename "$file")
    simpath="tests/Simulations/"$example
    testpath="tests/Telemetry/"$example"/telemetry.csv"
    clear; python3 main.py -s $simpath -t $testpath
done