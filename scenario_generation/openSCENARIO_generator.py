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

# group
ENTITY_KEY = "EntityObject"

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
    "VehicleCategory",
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

TOWN_TAG = 'LogicFile' # for finding out which town

class ScenarioGenerator:

    def __init__(self, save_dir:str, schema_file_path:str, path_to_basic_scenarios:str, number_scenarios:int):
        self.save_dir = save_dir
        self.number_scenarios = number_scenarios
        self.schema_file_path = schema_file_path
        self.path_to_basic_scenarios = path_to_basic_scenarios

        self.carla_info = {}
        self.values = _nested_dict()

    def run(self) -> None:

        # read schema file
        self.xmlSchema = self.readOpenScenarioSchema()
        self.inspect_schema()

        # read all basic scenarios and begin generation
        scenarioFilenames = [f for f in listdir(self.path_to_basic_scenarios) if isfile(join(self.path_to_basic_scenarios, f))]

        scenarioFiles = []
        for openScenrioFilename in scenarioFilenames:
            # read basic scenario and generate new Scenarios
            self.generateXmlScenariosFromBasic(openScenrioFilename)


    def fetch_data_from_carla(self, scenario_town: str) -> None:
        # TODO enrich categorial values for pedestrian group and vehicle.car types from CARLA server
        manipulator = ConfigManipulator(world_name=scenario_town)

        #The keys here match the keys in `changeable_attributes`
        #The mapping has to be done by hand though
        self.values['Vehicle']['name'] = manipulator.get_vehicle_actors()
        self.values['Pedestrian']['name'] = manipulator.get_actors('walker.')

        print(self.values)
        pass

    def inspect_schema(self) -> None:

        #print([val for val in self.xmlSchema.types['Weather'].iter_components()])
        #print(self.xmlSchema.types['Weather'].children)
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
                    self.values[value][a.name]


    def saveFile(self,data:str, file_name:str) -> None:
            if not os.path.exists(self.save_dir):
                os.makedirs(self.save_dir)
            with open(os.path.join(self.save_dir,f"{file_name}.xosc"),"w") as f:
                f.write(data)

    def readOpenScenarioSchema(self) -> xmlschema.validators.schema.XMLSchema10:
        return xmlschema.XMLSchema(self.schema_file_path)

    def prettify(self,elem:ET.ElementTree) -> str:
        rough_string = ElementTree.tostring(elem.getroot(), 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    def _check_duplication(self,new_scenario:ElementTree) -> bool:
        xml_hash = new_scenario.__hash__()

        for generatedFileHash in self.generated_scenarios_hashs:
            if xml_hash == generatedFileHash:
                 print("Duplication of generated file detected..")
                 return True

        return False

    def random_date(self,start) -> datetime.datetime:
        return start + datetime.timedelta(minutes=random.randrange(1440))

    def generateXmlScenariosFromBasic(self, openScenrioFilename: str):

        basic_scenario = ET.parse(self.path_to_basic_scenarios + openScenrioFilename)
        assert self.xmlSchema.is_valid(basic_scenario)

        new_scenario = basic_scenario
        root = new_scenario.getroot()

        # enrich possible values for pedestrian and car types from carla
        scenario_town = root.find(f'.//{TOWN_TAG}').items()[0][1]
        self.fetch_data_from_carla(scenario_town)

        # Change values -> save for the purpose of checking duplications
        self.generated_scenarios_hashs = []

        lowercased_restriction_values  = {k.lower(): v for k, v in self.restriction_values.items()}
        lowercased_complex_type_values = {k.lower(): v for k, v in self.complex_types.items()}

        for i in range(self.number_scenarios):

            date_time = datetime.datetime.now(pytz.timezone('Europe/Paris')).isoformat()

            # adapt fileheader changes
            root.find('FileHeader').set('author','3DCV-Generator')
            root.find('FileHeader').set('date',date_time)

            for tag in changeable_attributes:
                node = root.findall(f'.//{tag}')
                
                if len(node) == 1 and node is not None:
                     # special case: Time of day:
                    if node[0].tag == "TimeOfDay":
                        newDate = self.random_date(datetime.datetime(2020, 10, 3,00,00)).isoformat()
                        node[0].set("dateTime", str(newDate))

                    #set random values for complex types:
                    if node[0].tag.lower() in lowercased_complex_type_values.keys():
                        for item in node[0].items():
                            if item[0].lower() not in lowercased_restriction_values:
                                # TODO: what are realtsic ranges for those values ? 
                                if float(item[1]) != 0.0:
                                    new_value = float(item[1]) + float(item[1]) *random.uniform(-1,1)
                                else:
                                    new_value = float(random.uniform(0,10))

                                #print(f'before {item[0]}, {item[1]}')
                                node[0].set(item[0], str(new_value))
                                #print(f'after {node[0].items()}')

                    # set random value for restricted catagorial types:
                    for item in node[0].keys():
                        if item.lower() in lowercased_restriction_values.keys():
                            node[0].set(item,random.choice(lowercased_restriction_values[item.lower()]))

            #validate xosc again with schema
            assert self.xmlSchema.is_valid(new_scenario)


            #checking duplication
            if self._check_duplication(new_scenario):
                continue
            else:
                prettyfied_scenario = self.prettify(new_scenario)
                self.generated_scenarios_hashs.append(new_scenario.__hash__())
                self.saveFile(prettyfied_scenario, f"{os.path.splitext(openScenrioFilename)[0]}_{i}")

def _nested_dict():
    return defaultdict(_nested_dict)

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="")
    parser.add_argument('--number_scenarios', required=False, default=1, help="Number of Scenarios that should be created")
    parser.add_argument('--save_path',required=False, default="./generated_scenarios/", help="Path for saving XML scenario files")
    args = parser.parse_args()

    save_dir = args.save_path
    number_scenarios = args.number_scenarios

    XML_SCHEMA_FILE_PATH = "OpenSCENARIO.xsd"
    PATH_TO_BASIC_SCENARIOS = "./basic_scenarios/"

    #init
    generator = ScenarioGenerator(
        save_dir=save_dir,
        number_scenarios=number_scenarios,
        schema_file_path=XML_SCHEMA_FILE_PATH,
        path_to_basic_scenarios=PATH_TO_BASIC_SCENARIOS
        )

    # run generator
    generator.run()
