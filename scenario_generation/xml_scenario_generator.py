import xml.etree.cElementTree as ET
from xml.etree import ElementTree
from xml.dom import minidom
import argparse
import os
from os import listdir
from os.path import isfile, join
import random
import xmlschema
from pprint import pprint

town_list = [
    "Town01",
    "Town02",
    "Town03",
    "Town04",
    "Town05",
    "Town06",
    "Town07",
    "Town08",
    "Town09",
    "Town10"
]


class ScenarioGenerator:

    def __init__(self, save_dir:str, schema_file_path:str, path_to_basic_scenarios:str, number_scnearios:int):
        self.save_dir = save_dir
        self.number_scnearios = number_scnearios
        self.schema_file_path = schema_file_path
        self.path_to_basic_scenarios = path_to_basic_scenarios

    def run(self):
        # read schema file
        self.xmlSchema = self.readOpenScenarioSchema()
        self.inspect_schema()

        #  read basic scenario file
        # get all files in basic_scenario folder
        scenarioFilenames = [f for f in listdir(self.path_to_basic_scenarios) if isfile(join(self.path_to_basic_scenarios, f))]

        # validate all files
        scenarioFiles = []
        for openScenrioFilename in scenarioFilenames:
            # read basic scenario
            xt = ElementTree.parse(self.path_to_basic_scenarios + openScenrioFilename)
            assert self.xmlSchema.is_valid(xt)
            scenarioFiles.append(xt)

        # for first tests, just pick a scenario
        basic_scenario = scenarioFiles[1]

        #tree = self.generateXmlScenariosFromBasic(basic_scenario)

        #TODO call: self.save_files()


    def inspect_schema(self) -> None:
        for i in self.xmlSchema.iter_components():
            print(i)


    def save_files(self) -> None:
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        # TODO method for saving all generated scenario files
        # by calling self.savefile for file in self.generated_files with random file name based on basic scnerio name

    def saveFile(self,data:str, file_name:str) -> None:
            with open(os.path.join(self.save_dir,f"{file_name}.xosc"),"w") as f:
                f.write(tree)

    def readOpenScenarioSchema(self) -> xmlschema.validators.schema.XMLSchema10:
        return xmlschema.XMLSchema(self.schema_file_path)

    def prettify(self,elem:ET.ElementTree):
        rough_string = ElementTree.tostring(elem.getroot(), 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ")

    def generateXmlScenariosFromBasic(self, basic_scenario: ET.ElementTree) -> list:

        pprint(self.xmlSchema.to_dict(basic_scenario))

        generated_scenarios = []

        for i in range(self.number_scnearios):
            generated_scenarios.append("bla")

        return generated_scenarios


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="")
    parser.add_argument('--number_scnearios', required=False, default=5,help="Number of Scenarios that should be created")
    parser.add_argument('--save_path',required=False, default="./generated_scenarios/",help="Path for saving XML scneario file")
    args = parser.parse_args()

    save_dir = args.save_path
    number_scnearios = args.number_scnearios

    XML_SCHEMA_FILE_PATH = "OpenSCENARIO.xsd"
    PATH_TO_BASIC_SCENARIOS = "./basic_scenarios/"

    #init
    generator = ScenarioGenerator(
        save_dir=save_dir,
        number_scnearios=number_scnearios,
        schema_file_path=XML_SCHEMA_FILE_PATH,
        path_to_basic_scenarios=PATH_TO_BASIC_SCENARIOS
        )

    # run generator
    generator.run()
