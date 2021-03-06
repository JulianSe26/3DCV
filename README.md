# 3DCV project on critical driving scenarios

Christopher Klammt  
Tobias Richstein  
Julian Seibel  
Karl Thyssen


[Link to the report](report/report.pdf)


## Scenario generation

To start the scenario generation, make sure to install all requirements using the *environment.yml* i.e. with conda:

`` conda env create -f environment.yml ``

Apart from that the CARLA Python package needs to be installed as described in [the CARLA documentation](https://carla.readthedocs.io/en/latest/start_quickstart/#b-package-installation).


(This step is not needed if you only want to use the basic scenarios provided with CARLA v0.9.9) Afterwards, make sure to place all basic scenarios in the *./scenario_generation/basic_scenarios/* folder as *xosc* OpenSCENARIO configuration files.

Start the process by executing the following command from the root folder:

``python ./scenario_generation/openSCENARIO_generator.py [--log] [--number_scenarios] [--save_path]``

Explanation of the arguments:
* ``logs`` : Flag, whether logging should be activated. The generator will save one csv file per basic scenario in *./logs/* that includes all new values set for newly generated scenarios
* ``number_scenarios`` : The number of scenarios which should be created from one basic scenario (*default* is 1)
* ``save_path`` : Folder where to save the generated scenarios (*default* is *./generated_scenarios/*)

**Note** : To start the Scenario-Generator, make sure you have a running CARLA v0.9.9 instance. The scripts will use the Python-API of the CARLA Server.

Below are some examples of newly generated scenarios compared to the original scenario.

### Cyclist scenario
![Original cyclist scenario](report/figures/generated/cyclist_original.jpg)

Above is the original blueprint for the cyclist scenario. It features a hero car and a bike that is about to cross the street forcing the car to brake.

---

![Modified cyclist scenario in same town](report/figures/generated/cyclist_1.jpg)
This is a modified scenario of the cyclist crossing. The bike has been replaced with a car and the situation occurs at a different intersection but within the same map.

---

![Modified cyclist scenario in different town](report/figures/generated/cyclist_2.jpg)

For this scenario the town has changed but the parameters of the situation remain the same.


### Lane Changing Scenario

![Original lane changing scenario](report/figures/generated/lanechange_original.jpg)

This scenario describes the hero car following a car driving in front that abruptly changes its lane to avoid a still standing vehicle.

---

![Modified lane changing scenario in same town](report/figures/generated/lanechange_1.jpg)

This generated scenario takes place in rougher weather and also features the highway going in the other direction than in the original and also using a different lane.

---

![Modified lane changing scenario in a different town](report/figures/generated/lanechange_2.jpg)

Above we can see a generated lane changing scenario taking place in a different town from the original scenario.


## Data generation

To collect data for some generated scenarios, you have to replace the *manual_control.py*-file of the Scenario-Runner with the one provided in the data_generation folder. Then (with CARLA running) you just need to execute the *run.cmd*-file (currently only for Windows).
This will:
- generate the specified amount of scenarios per base scenario (currently defined with 5 in the *run.cmd*)
- for each generated scenario, run it via the Scenario-Runner
- and start the *manual_control.py* in autopilot mode to gather the data with the expert driving

You can find the collected data in form of image-files and measurements.json (expert control input) inside the *_out* folder in the Scenario-Runner.
