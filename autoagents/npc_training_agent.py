#!/usr/bin/env python

# This work is licensed under the terms of the MIT license.
# For a copy, see <https://opensource.org/licenses/MIT>.

"""
This module provides an NPC agent to control the ego vehicle
"""

from __future__ import print_function

import os
import json
from PIL import Image as PImage

import carla
from agents.navigation.basic_agent import BasicAgent

from srunner.autoagents.autonomous_agent import AutonomousAgent
from srunner.scenariomanager.carla_data_provider import CarlaDataProvider


class TrainingNpcAgent(AutonomousAgent):

    """
    NPC autonomous agent to control the ego vehicle and record each step
    """

    _agent = None
    _route_assigned = False

    def setup(self, path_to_conf_file):
        """
        Setup the agent parameters
        """
        # Here we instantiate a sample carla settings. The name of the configuration should be
        # passed as a parameter.

        self._settings_module = __import__(path_to_conf_file)
        # self._episode_path = self._settings_module.EPISODE_PATH TODO: add the EPISODE_PATH to scenario config file

        self._episode_path = './dataset/exp1/episode_00001/'
        self.setup_recording(self._episode_path)
        self._route_assigned = False
        self._agent = None
        self._image_number = 0

    def sensors(self):
        """
        Define the sensor suite required by the agent

        :return: a list containing the required sensors in the following format:
        """

        sensors = [
            {'type': 'sensor.camera.rgb', 'x': 0.7, 'y': -0.4, 'z': 1.60, 'roll': 0.0, 'pitch': 0.0, 'yaw': 0.0,
             'width': self._settings_module['width'], 'height': self._settings_module['height'], 'fov': self._settings_module['fov'], 'id': 'Left'},
        ]

        return sensors

    def run_step(self, input_data, timestamp):
        """
        Execute one step of navigation.
        """
        control = carla.VehicleControl()
        control.steer = 0.0
        control.throttle = 0.0
        control.brake = 0.0
        control.hand_brake = False

        self.save_data(control, input_data)
        self._image_number = self._image_number + 1
        
        if not self._agent:
            hero_actor = None
            for actor in CarlaDataProvider.get_world().get_actors():
                if 'role_name' in actor.attributes and actor.attributes['role_name'] == 'hero':
                    hero_actor = actor
                    break
            if hero_actor:
                self._agent = BasicAgent(hero_actor)

            return control

        if not self._route_assigned:
            if self._global_plan:
                plan = []

                for transform, road_option in self._global_plan_world_coord:
                    wp = CarlaDataProvider.get_map().get_waypoint(transform.location)
                    plan.append((wp, road_option))

                self._agent._local_planner.set_global_plan(plan)  # pylint: disable=protected-access
                self._route_assigned = True

        else:
            control = self._agent.run_step()



        return control


    def save_data(self, control, input_data):
        '''
        save the data for each step
        '''
        # Save RGB
        for name, data in input_data.items():
            #Image.fromarray(data).save(os.path.join(self._episode_path, name + '_' + self._image_number.zfill(5)), '.png')
            data.save_to_disk(os.path.join(self._episode_path, name + '_' + self._image_number.zfill(5)), '.png')
        
        # Save Measurements
        with open(os.path.join(self._episode_path, 'measurements_' + self._image_number.zfill(5) + '.json'), 'w') as fo:
            jsonObj = {}
            jsonObj.update({'steer': control.steer})
            jsonObj.update({'throttle': control.throttle})
            jsonObj.update({'brake': control.brake})
            jsonObj.update({'hand_brake': control.hand_brake})
            jsonObj.update({'reverse': control.reverse})
            jsonObj.update({'steer_noise': 0})
            jsonObj.update({'throttle_noise': 0})
            jsonObj.update({'brake_noise': 0})

            fo.write(json.dumps(jsonObj, sort_keys=True, indent=4))

    def setup_recording(self, dataset_path):
        '''
        make dataset path
        make episode metadata

        '''
        # Create episode directory
        if not os.path.exists(dataset_path):
            os.makedirs(dataset_path)

        # Create episode metadata.json
        with open(os.path.join(dataset_path, 'metadata.json'), 'w') as fo:
            jsonObj = {}
            jsonObj.update(self._settings_module.sensors_yaw)
            jsonObj.update({'fov': self._settings_module.FOV})
            jsonObj.update({'width': self._settings_module.WINDOW_WIDTH})
            jsonObj.update({'height': self._settings_module.WINDOW_HEIGHT})
            jsonObj.update({'lateral_noise_percentage': 0})
            jsonObj.update({'longitudinal_noise_percentage': 0})
            jsonObj.update({'car range': self._settings_module.NumberOfVehicles})
            jsonObj.update({'pedestrian range': self._settings_module.NumberOfPedestrians})
            jsonObj.update({'set_of_weathers': self._settings_module.set_of_weathers})
            jsonObj.update({'scenario_config_path': self._settings_module.scenario_config_path})
            fo.write(json.dumps(jsonObj, sort_keys=True, indent=4))
