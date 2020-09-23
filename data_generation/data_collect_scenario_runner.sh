#!/bin/bash

#run using ./data_collect_scenario_runner.sh --number_of_scenarios --resolution
python3 openSCENARIO_generator.py --$1

counter = 1
for scenario in ./generated_scenarios/*
do
scenario_runner.py --openscenario $scenario
manual_control.py --episode $counter -a --res $2
counter = $((counter+1))
done

sudo chmod a+x data_collect_scenario_runner.sh