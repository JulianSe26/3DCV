import carla
import random
from typing import List
import itertools
import math
import numpy as np
from collections import defaultdict

class ConfigManipulator:
    def __init__(self, world_name: str = "Town01", host: str = "localhost", port: int = 2000):
        self.client = carla.Client(host, port)
        self.load_world(world_name)

        self.world = self.client.get_world()

        self.world_vehicle_actors = defaultdict(list)
        self.world_walker_actors = defaultdict(list)
        self.scene_analysis = defaultdict(dict)

    def load_world(self, world_name: str):
        try:
            #print(not hasattr(self, 'map') or not self.map.name == world_name)
            if not hasattr(self, 'map') or not self.map.name == world_name:
                self.client.load_world(world_name)
                self.map = self.client.get_world().get_map()
        except RuntimeError:
            pass


    def get_pos_in_distance(self, x:int, y:int, z:int, distance:float) -> carla.Waypoint:
        """Get a new `carla.Waypoint` at a set distance from the current location. 
        Returned waypoints are guaranteed to be on the same road and lane.
        """
        m = self.world.get_map()

        s = m.get_waypoint(carla.Location(x=x, y=y, z=z)).previous(distance)

        if len(s) > 0:
            return s[0]

    def get_vehicle_actors(self, wheels:int=4) -> List[str]:
        """This is a little janky but filtering by the number of wheels seems to be the easiest method to filter out cars/bikes from pedestrians"""
        return [a.id for a in self.world.get_blueprint_library().filter('vehicle') if a.get_attribute('number_of_wheels').as_int() == wheels]

    def get_actors(self, filter:str='*') -> List[str]:
        """Return all possible actors in the world or filter by regex"""
        return [bp.id for bp in self.client.get_world().get_blueprint_library().filter(filter)]

    def get_random_actor(self, filter:str='*') -> str:
        """Get the name of a random actor. Filter can be used to only select certain categories.
        `vehicle` for cars only, `static` for props, `walker` for people
        Default is `*`
        """
        return random.choice(self.get_actors(filter=filter))

    def get_random_vehicle_actor(self, wheels:int=4) -> str:
        """Returns string for a vehicle with `wheels` many wheels
        """
        return random.choice(self.get_vehicle_actors())

    def rotate2d(self, x:float, y:float, radians:float):
        """required helper method to rotate a 2d vector by radians
        """
        c, s = np.cos(radians), np.sin(radians)
        j = np.matrix([[c, s], [-s, c]])
        m = np.dot(j, [x, y])
        return float(m.T[0]), float(m.T[1])

    def map_query_actors(self, world_name: str = "Town01"):
        self.load_world(world_name)
        self.world_vehicle_actors[world_name] = self.get_vehicle_actors()
        self.world_walker_actors[world_name] = self.get_actors(filter='walker.*')

    def get_transform_from_pos(self, pos) -> carla.Waypoint:
        return carla.Transform(carla.Location(x=pos['x'], y=pos['y'], z=pos['z']), carla.Rotation(yaw=pos['yaw']))

    def lc_analysis(self, scene_name='LaneChangeSimple.xosc', hero_pos=None, adv_pos=None, s_pos=None):
        if hero_pos is None or adv_pos is None:
            v = [a for a in self.world.get_actors() if 'role_name' in a.attributes.keys() and a.attributes['role_name'] == 'hero'][0].get_transform()
            b = [a for a in self.world.get_actors() if 'role_name' in a.attributes.keys() and a.attributes['role_name'] == 'adversary'][0].get_transform()
            s = [a for a in self.world.get_actors() if 'role_name' in a.attributes.keys() and a.attributes['role_name'] == 'standing'][0].get_transform()
        else:
            v = self.get_transform_from_pos(hero_pos)
            b = self.get_transform_from_pos(adv_pos)
            s = self.get_transform_from_pos(s_pos)

        wpv = self.map.get_waypoint(v.location)

        self.scene_analysis[scene_name] = {'wpv': wpv, 'v': v, 'b': b, 's':s}


    def lc_scenario(self, scene_name='LaneChangeSimple.xosc'):

        if len(self.scene_analysis[scene_name].keys()) < 4:
            self.lc_analysis()

        v = self.scene_analysis[scene_name]['v']
        b = self.scene_analysis[scene_name]['b']
        s = self.scene_analysis[scene_name]['s']
        wpv = self.scene_analysis[scene_name]['wpv']

        eligible_spawns = []

        # iterate over spawn points and check if the spawn point satisfies scenario conditions
        for spawn_point in self.map.get_spawn_points():
            spawn_waypoint = self.map.get_waypoint(spawn_point.location)
            adv_waypoints = spawn_waypoint.next(wpv.transform.location.distance(b.location))
            standing_waypoints = spawn_waypoint.next(wpv.transform.location.distance(s.location))
            if spawn_waypoint.lane_type == carla.LaneType.Driving and (spawn_waypoint.lane_change == carla.LaneChange.Left or spawn_waypoint.lane_change == carla.LaneChange.Both) and len(standing_waypoints) == 1 and standing_waypoints[0].lane_type == carla.LaneType.Driving and (standing_waypoints[0].lane_change == carla.LaneChange.Left or standing_waypoints[0].lane_change == carla.LaneChange.Both) and abs(adv_waypoints[0].transform.rotation.yaw - standing_waypoints[0].transform.rotation.yaw) < 10:
                eligible_spawns.append(spawn_waypoint)

        # calculate all new spawns
        h = random.choice(eligible_spawns)
        new_hero_spawn = (h.transform.location.x, h.transform.location.y, math.radians(h.transform.rotation.yaw))
        new_adv_spawn = [(a.transform.location.x, a.transform.location.y, math.radians(a.transform.rotation.yaw)) for a in h.next(wpv.transform.location.distance(b.location))][0]
        new_standing_spawn = [(a.transform.location.x, a.transform.location.y, math.radians(a.transform.rotation.yaw)) for a in h.next(wpv.transform.location.distance(s.location))][0]

        return new_hero_spawn, new_adv_spawn, new_standing_spawn

    def cyclist_scenario(self, hero_pos=None, adv_pos=None):
        if hero_pos is None or adv_pos is None:
            # Get location of vehicle v and bike b. Then get their closest waypoints
            v = [a for a in self.world.get_actors() if 'role_name' in a.attributes.keys() and a.attributes['role_name'] == 'hero'][0].get_transform()
            b = [a for a in self.world.get_actors() if 'role_name' in a.attributes.keys() and a.attributes['role_name'] == 'adversary'][0].get_transform()
        else:
            v = self.get_transform_from_pos(hero_pos)
            b = self.get_transform_from_pos(adv_pos)

        wpv = self.map.get_waypoint(v.location)
        ptb = b
        wpb = self.map.get_waypoint(b.location)

        # get all junctions described by the map topology and order them according to their distance to the hero
        # The closest junction (when driving forward) is the 'base junction' that is used as the scenario anchor
        wp = [a for a in list(itertools.chain(*self.world.get_map().get_topology())) if a.is_junction]
        dists = sorted(wpv.transform.location.distance(a.transform.location) for a in wp)
        for i in dists:
            if wpv.next(i)[0].is_junction:
                closest_junction = wpv.next(i)[0]
                break

        bike_spawn_wp = []
        new_car_spawn_wp_good = False
        i = 0

        delta_x = wpv.transform.location.x - closest_junction.transform.location.x

        # Not all positions calculated actually work. Therefore we include two sanity checks 
        while len(bike_spawn_wp) == 0 or not new_car_spawn_wp_good:

            # Choose a random junction on the map 
            new_junction = random.choice(wp)

            # Get the hero's new waypoint including heading in relation to the new junction
            # Declare the spawn point as valid if the car's yaw is roughly the same as the junction's yaw
            new_car_spawn = [(a.transform.location.x, a.transform.location.y, a.transform.rotation.yaw) for a in new_junction.previous(wpv.transform.location.distance(closest_junction.transform.location))][0]
            new_car_spawn_wp_good = abs(new_junction.transform.rotation.yaw - new_car_spawn[2]) < 45

            # Calculate the new spawn point of the bike
            # Get a waypoint that is the same distance away from the base junction as in the base scenario
            # Check if the relation of the hero's and adversary's heading matches at the new wp
            #bike_spawn_wp = [(a.transform.location.x, a.transform.location.y, a.transform.location.z, a.transform.rotation.yaw) for a in new_junction.next(closest_junction.transform.location.distance(wpb.transform.location)) if abs((a.transform.rotation.yaw - new_car_spawn[2]) - (wpb.transform.rotation.yaw - wpv.transform.rotation.yaw)) < 50
            bike_spawn_wp = [(a.transform.location.x, a.transform.location.y, a.transform.location.z, a.transform.rotation.yaw) for a in new_junction.next(delta_x) if abs((a.transform.rotation.yaw - new_car_spawn[2]) - (wpb.transform.rotation.yaw - wpv.transform.rotation.yaw)) < 50]
            i+=1


        # The bike's position is not considered a waypoint by carla. However it is way easier using waypoints for calculations so we calculate an offset to the bike's closest waypoint
        # that we will later reapply 
        bike_offset = (ptb.location.x - wpb.transform.location.x, ptb.location.y - wpb.transform.location.y, math.radians(wpb.transform.rotation.yaw - bike_spawn_wp[0][3]))

        #print('required {} iterations to find new spawn'.format(i))
        new_offset = self.rotate2d(*bike_offset)
        new_bike_spawn = (bike_spawn_wp[0][0] + new_offset[0], bike_spawn_wp[0][1] + new_offset[1], math.radians(new_car_spawn[2]))
        new_car_spawn = list(new_car_spawn)
        new_car_spawn[2] = math.radians(new_car_spawn[2])
        new_car_spawn = tuple(new_car_spawn)

        return new_car_spawn, new_bike_spawn


if __name__ == "__main__":
    
    pass
