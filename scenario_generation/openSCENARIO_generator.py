import xml.etree.cElementTree as ET
from xml.etree import ElementTree
from xml.etree.ElementTree import fromstring, ElementTree as XET
from xml.dom import minidom
import argparse
import os
from os import listdir
from os.path import isfile, join
import random
import xmlschema
import datetime
import pytz
from collections import defaultdict
from hashlib import md5
from manipulator import ConfigManipulator
from values import GeneratorValues, ValTypes
import math
import tqdm
import sys
import copy

# complex types
schema_complex_types_values = [
    "Sun",
    "Fog",
    "DynamicConstraints",
    "Precipitation"
]

# value restrictions
schema_restriction_values = [
    "CloudState",
    "RouteStrategy",
    "MiscObjectCategory",
    "ObjectType",
    "PrecipitationType",
   # "VehicleCategory",  -> need some more attention
    "Rule",
    "PedestrianCategory",
    "RouteStrategy"
]

# attributes to change
changeable_attributes = [
    'Vehicle',
    'Pedestrian',
    'Weather',
    'Fog',
    'Sun',
    'Precipitation',
    'RoadCondition',
    'TimeOfDay',
    'MiscObject'
]

TownList = [
    'Town01',
    'Town02',
    'Town03',
    'Town04',
    'Town05'
]

TOWN_TAG = 'LogicFile' # for finding out which town is used

class ScenarioGenerator:

    def __init__(self, save_dir:str, schema_file_path:str, path_to_basic_scenarios:str, number_scenarios:int):
        self.save_dir = save_dir
        self.number_scenarios = int(number_scenarios)
        self.schema_file_path = schema_file_path
        self.path_to_basic_scenarios = path_to_basic_scenarios
        self.manipulator = None
        self.values = _nested_dict()
        self.manipulator = ConfigManipulator()

    def run(self) -> None:

        # read schema file
        self.xmlSchema = self.readOpenScenarioSchema()
        self.inspect_schema()

        # read all basic scenarios and begin generation
        scenarioFilenames = [f for f in listdir(self.path_to_basic_scenarios) if isfile(join(self.path_to_basic_scenarios, f))]

        for town in TownList:
            self.manipulator.map_query_actors(town)

        scenarioFiles = []
        for openScenarioFilename in scenarioFilenames:
            # read basic scenario and generate new Scenarios
            self.generateXmlScenariosFromBasic(openScenarioFilename)


    def fetch_data_from_carla(self, scenario_town: str) -> None:
        #The keys here match the keys in `changeable_attributes`
        #The mapping has to be done by hand though
        self.values['Vehicle']['name'] = GeneratorValues(ValTypes.CATEGORICAL, self.manipulator.world_vehicle_actors[scenario_town], None) 
        self.values['Pedestrian']['name'] = GeneratorValues(ValTypes.CATEGORICAL, self.manipulator.world_walker_actors[scenario_town], None)

        pass

    def inspect_schema(self) -> None:
        ''' Function for inspecting schema file of openSCENARIO Standard and build attribute tree '''

        # all restrictions for possible values
        self.restriction_values = {}
        for value in schema_restriction_values:
            self.restriction_values.update({value: self.xmlSchema.types[value].member_types[0].enumeration})

        # all changeable, complex types
        self.complex_types = {}
        for value in schema_complex_types_values:
            self.complex_types.update({value: self.xmlSchema.types[value].attributes.keys()})

        # For now just get the keys that the changeable attribute itself has
        for value in changeable_attributes:
            for a in self.xmlSchema.types[value].iter_components():
                if type(a) == xmlschema.XsdAttribute:   
                    self.values[value][a.name] = GeneratorValues(ValTypes.get_key_for_val(a.type.name))
                    if a.type.name in schema_restriction_values:
                        self.values[value][a.name].val = self.xmlSchema.types[a.type.name].member_types[0].enumeration


    def saveFile(self,data:str, file_name:str) -> None:
            if not os.path.exists(self.save_dir):
                os.makedirs(self.save_dir)
            with open(os.path.join(self.save_dir,f"{file_name}.xosc"),"w") as f:
                f.write(data)

    def readOpenScenarioSchema(self) -> xmlschema.validators.schema.XMLSchema10:
        return xmlschema.XMLSchema(self.schema_file_path)

    def prettify(self,elem:ET.ElementTree) -> str:
        ''' Prettify XMl string for saving it as file '''
        rough_string = ElementTree.tostring(elem.getroot(), 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    def _check_duplication(self,new_scenario:ElementTree) -> bool:
        ''' Helper function for detecting duplication in generated files using its hash '''
      
        if self._getStringHashOfFile(new_scenario) in self.generated_scenarios_hashs:
                 print("Duplication of generated file detected..")
                 return True
        else:
                return False

    def _getStringHashOfFile(self, scenario_tree:ElementTree):
        '''
         Helper function for getting a hash value of string based content. 
         Assumption: There is no disordering of attributes during the generation process
        '''
        xml_hash_string = ElementTree.tostring(scenario_tree.getroot(),'utf-8')
        return b''.join(xml_hash_string.split()).__hash__

    def _generateRandomRGB(self):
        return [str(random.randint(0,255)) for i in range(3)]

    def random_date(self,start) -> datetime.datetime:
        ''' Helper function for generating a new date in range 00:00 AM and 23:59 PM '''
        return start + datetime.timedelta(minutes=random.randrange(1440))

    def generateXmlScenariosFromBasic(self, openScenarioFilename: str):
        ''' Generate Scenario by using basic scenario as template '''

        basic_scenario = ET.parse(self.path_to_basic_scenarios + openScenarioFilename)
        assert self.xmlSchema.is_valid(basic_scenario)

        root_original = basic_scenario.getroot()
        
        # enrich possible values for pedestrian and car types from carla
        scenario_town = root_original.find(f'.//{TOWN_TAG}').items()[0][1]

        # generate random based pre selection of town for every new scenario to optimize workload
        scenario_towns = [TownList[random.randint(0, len(TownList)-1)] for n in range(self.number_scenarios)]
        scenario_towns.sort()

        # Change values -> save for the purpose of checking duplications
        self.generated_scenarios_hashs = []

        lowercased_restriction_values  = {k.lower(): v for k, v in self.restriction_values.items()}
        lowercased_complex_type_values = {k.lower(): v for k, v in self.complex_types.items()}

        self.manipulator.load_world(scenario_town)

        if openScenarioFilename == 'LaneChangeSimple.xosc':
            self.manipulator.lc_analysis(openScenarioFilename, self.get_pos_for_role(root_original, 'hero'), self.get_pos_for_role(root_original, 'adversary'), self.get_pos_for_role(root_original, 'standing'))
        elif openScenarioFilename == 'CyclistCrossing.xosc':
            self.manipulator.cyclist_analysis(openScenarioFilename, self.get_pos_for_role(root_original, 'hero'), self.get_pos_for_role(root_original, 'adversary'))

        for i in tqdm.tqdm(range(self.number_scenarios), desc=f"Generating new Scenarios for base scenario {openScenarioFilename}", file=sys.stdout):

            #TODO: load selected town for new scenario
            #print(scenario_towns[i])

            # HACK: only switch town in supported scenarios
            if openScenarioFilename == 'LaneChangeSimple.xosc' or openScenarioFilename == 'CyclistCrossing.xosc':
                this_town = scenario_towns[i]
            else:
                this_town = scenario_town

            self.manipulator.load_world(this_town)
            self.fetch_data_from_carla(this_town)
            
            # get a deep copy of basic scenario to not change it
            new_scenario = copy.deepcopy(basic_scenario)
            root = new_scenario.getroot()
            date_time = datetime.datetime.now(pytz.timezone('Europe/Paris')).isoformat()

            # adapt fileheader changes
            root.find('FileHeader').set('author','CARLA:3DCV-Generator')
            root.find('FileHeader').set('date', date_time)

            for tag in self.values.keys():
                nodes = root.findall(f'.//{tag}')
                
                if len(nodes) > 0:
                    for node in nodes: 
                     # special case: Time of day:
                        if node.tag == "TimeOfDay":
                            newDate = self.random_date(datetime.datetime(2020, 10, 3,00,00)).isoformat()
                            node.set("dateTime", str(newDate))
                            continue

                        items = node.items()
                
                        for (item_tag, gen_vals) in self.values[tag].items():
                            item = [a for a in items if a[0] == item_tag][0]
                            if gen_vals.type == ValTypes.DOUBLE:
                                if float(item[1]) != 0.0:
                                    new_value = float(item[1]) + float(item[1]) *random.uniform(-1,1)
                                else:
                                    new_value = float(random.uniform(0,10))
                            elif gen_vals.type == ValTypes.CATEGORICAL and len(gen_vals.val) > 0:
                                new_value = random.choice(gen_vals.val)  
                            else:
                                continue
                            node.set(item[0], str(new_value))
                else:
                      continue

            root.find(f'.//{TOWN_TAG}').set('filepath', this_town)

            if openScenarioFilename == 'CyclistCrossing.xosc':
                new_car_spawn, new_bike_spawn = self.manipulator.cyclist_scenario()
                for actor in root.find('Storyboard').find('Init').find('Actions').findall('Private'):
                    pos = actor.find('PrivateAction').find('TeleportAction').find('Position').find('WorldPosition')
                    if actor.get('entityRef') == 'hero':
                        spawn = new_car_spawn
                    elif actor.get('entityRef') == 'adversary':
                        spawn = new_bike_spawn
                    pos.set('x', str(spawn[0]))
                    pos.set('y', str(spawn[1]))
                    pos.set('h', str(spawn[2]))
                    pos.set('z', str(float(pos.get('z')) + .5))
            elif openScenarioFilename == 'LaneChangeSimple.xosc':
                try:
                    new_hero_spawn, new_adv_spawn, new_standing_spawn = self.manipulator.lc_scenario()
                    for actor in root.find('Storyboard').find('Init').find('Actions').findall('Private'):
                        pos = actor.find('PrivateAction').find('TeleportAction').find('Position').find('WorldPosition')
                        if actor.get('entityRef') == 'hero':
                            spawn = new_hero_spawn
                        elif actor.get('entityRef') == 'adversary':
                            spawn = new_adv_spawn
                        elif actor.get('entityRef') == 'standing':
                            spawn = new_standing_spawn
                        pos.set('x', str(spawn[0]))
                        pos.set('y', str(spawn[1]))
                        pos.set('h', str(spawn[2]))
                        pos.set('z', str(float(pos.get('z')) + .5))
                except IndexError:
                    break

            # change color of vehicle randomly if color attribute is available
            for scenario_obj in root.find('Entities').findall('ScenarioObject'):
                try:
                    for p in scenario_obj.find('Vehicle').find('Properties').findall('Property'):
                        if p.get("name") == 'color':
                           p.set("value", ",".join(self._generateRandomRGB()))
                except:
                   pass

            #validate xosc again with schema
            assert self.xmlSchema.is_valid(new_scenario)

            #checking duplication
            if self._check_duplication(new_scenario):
                 continue
            else:
                prettyfied_scenario = self.prettify(new_scenario)
                self.generated_scenarios_hashs.append(self._getStringHashOfFile(new_scenario))
                self.saveFile(prettyfied_scenario, f"{os.path.splitext(openScenarioFilename)[0]}_{i}")

    def get_pos_for_role(self, scenario_root, role:str) -> tuple:
        ''' Helper function for finding spawn positions for included actors '''
        actor = [a for a in scenario_root.find('Storyboard').find('Init').find('Actions').findall('Private') if a.get('entityRef') == role][0]
        pos = actor.find('PrivateAction').find('TeleportAction').find('Position').find('WorldPosition')
        return {'x': float(pos.get('x')), 'y': float(pos.get('y')), 'z': float(pos.get('z')), 'yaw': math.degrees(float(pos.get('h')))}

def _nested_dict():
    return defaultdict(_nested_dict)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="")
    parser.add_argument('--number_scenarios', required=False, default=1, help="Number of Scenarios that should be created")
    parser.add_argument('--save_path',required=False, default="./generated_scenarios/", help="Path for saving XML scenario files")
    args = parser.parse_args()

    save_dir = args.save_path
    number_scenarios = args.number_scenarios

    XML_SCHEMA_FILE_PATH = "scenario_generation/OpenSCENARIO.xsd"
    PATH_TO_BASIC_SCENARIOS = "scenario_generation/basic_scenarios/"

    #init
    generator = ScenarioGenerator(
        save_dir=save_dir,
        number_scenarios=number_scenarios,
        schema_file_path=XML_SCHEMA_FILE_PATH,
        path_to_basic_scenarios=PATH_TO_BASIC_SCENARIOS
        )

    # run generator
    generator.run()

    print("Successfully finished")
