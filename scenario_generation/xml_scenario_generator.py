import xml.etree.cElementTree as ET
from xml.etree import ElementTree
from xml.dom import minidom
import argparse
import os
import random

# TODO: Specify which parameters should be changed

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

wheater_list=[
    "tbd."
]

car_models = [
    "vehicle.lincoln.mkz2017",
    "tbd."
]

def prettify(elem):
    rough_string = ElementTree.tostring(elem.getroot(), 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ")

def generate_xml_scenario(number_scnearios:int) -> ET.ElementTree:
    root = ET.Element("scenarios")

    for i in range(number_scnearios):
         # TODO: randomize or vary parameters for every loop step
        scenario = ET.SubElement(root, "scenario", name=f"scnearioName_{i}",type="todo",town=random.choice(town_list))
        # TODO: in which ranges are coordinates lying ? 
        ET.SubElement(scenario, "ego_vehicle", x="1",y="2",z="3",yaw="4", model="vehicle.lincoln.mkz2017")
        ET.SubElement(scenario, "other_actor", x="2",y="3",z="4",yaw="5",model="vehicle.tesla.model3")
        ET.SubElement(scenario,"target", x="899999", y="2323023", z="1.0")

        #TODO: which elements does exist in general ?
        #  <other_actor random_location="True" autopilot="True" model="vehicle.*" amount="50" /> --> differs i.e. from obove

        tree = ET.ElementTree(root)

    return tree

parser = argparse.ArgumentParser(description="")
parser.add_argument('--number_scnearios', required=False, default=5,help="Number of Scenarios that should be created")
parser.add_argument('--file_name', required=True,help="Name of XML scneario file")
parser.add_argument('--save_path',required=False, default="./generated_scenarios/",help="Path for saving XML scneario file")
args = parser.parse_args()

save_dir = args.save_path
number_scnearios = args.number_scnearios
file_name = args.file_name

if not os.path.exists(save_dir):
    os.makedirs(save_dir)

tree = generate_xml_scenario(number_scnearios)

tree = prettify(tree)

with open(os.path.join(save_dir,f"{file_name}.xml"),"w") as f:
    f.write(tree)