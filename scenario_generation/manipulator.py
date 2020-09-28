import carla
import random
from typing import List
import itertools
import math
import numpy as np

class ConfigManipulator:
    def __init__(self, world_name: str = "Town01", host: str = "localhost", port: int = 2000):
        self.client = carla.Client(host, port)
        self.client.load_world(world_name)
        self.world = self.client.get_world()


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

    def get_random_in_range(low:int=0, high=10):
        """Get random number where low <= num <= high
        `high` determines the return type. If it is a `float` return a float. If it is `int` return an int.
        """
        if type(high) == 'int':
            return random.randint(low, high)
        elif type(high) == 'float':
            return random.uniform(low, high)

    def get_random_from_list(data:list, num:int=1):
        """Get `num` entries from a list
        """
        return random.choices(data, k=num)

    def rotate2d(self, x:float, y:float, radians:float):
        """required helper method to rotate a 2d vector by radians
        """
        c, s = np.cos(radians), np.sin(radians)
        j = np.matrix([[c, s], [-s, c]])
        m = np.dot(j, [x, y])
        return float(m.T[0]), float(m.T[1])

    def get_transform_from_pos(self, pos) -> carla.Waypoint:
        return carla.Transform(carla.Location(x=pos['x'], y=pos['y'], z=pos['z']), carla.Rotation(yaw=pos['yaw']))


    def cyclist_scenario(self, hero_pos=None, adv_pos=None):


        if hero_pos is None or adv_pos is None:
            # Get location of vehicle v and bike b. Then get their closest waypoints
            v = [a for a in self.world.get_actors() if 'role_name' in a.attributes.keys() and a.attributes['role_name'] == 'hero'][0].get_transform()
            b = [a for a in self.world.get_actors() if 'role_name' in a.attributes.keys() and a.attributes['role_name'] == 'adversary'][0].get_transform()
        else:
            v = self.get_transform_from_pos(hero_pos)
            b = self.get_transform_from_pos(adv_pos)

        wpv = self.world.get_map().get_waypoint(v.location)
        ptb = b
        wpb = self.world.get_map().get_waypoint(b.location)

        # get all junctions described by the map topology and order them according to their distance to the hero
        # The closest junction (when driving forward) is the 'base junction' that is used as the scenario anchor
        wp = [a for a in list(itertools.chain(*self.world.get_map().get_topology())) if a.is_junction]
        dists = sorted(wpv.transform.location.distance(a.transform.location) for a in wp)
        for i in dists:
            if wpv.next(i)[0].is_junction:
                closest_junction = wpv.next(i)[0]
                break
        print(wpv)
        print(wpb)
        print(closest_junction)

        bike_spawn_wp = []
        new_car_spawn_wp_good = False
        i = 0

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
            #bike_spawn_wp = [(a.transform.location.x, a.transform.location.y, a.transform.location.z, a.transform.rotation.yaw) for a in new_junction.next(closest_junction.transform.location.distance(wpb.transform.location)) if abs((a.transform.rotation.yaw - new_car_spawn[2]) - (wpb.transform.rotation.yaw - wpv.transform.rotation.yaw)) < 50]
            bike_spawn_wp = [(a.transform.location.x, a.transform.location.y, a.transform.location.z, a.transform.rotation.yaw) for a in new_junction.next(23) if abs((a.transform.rotation.yaw - new_car_spawn[2]) - (wpb.transform.rotation.yaw - wpv.transform.rotation.yaw)) < 50]
            
            i+=1


        # The bike's position is not considered a waypoint by carla. However it is way easier using waypoints for calculations so we calculate an offset to the bike's closest waypoint
        # that we will later reapply 
        bike_offset = (ptb.location.x - wpb.transform.location.x, ptb.location.y - wpb.transform.location.y, math.radians(wpb.transform.rotation.yaw - bike_spawn_wp[0][3]))

        print('required {} iterations to find new spawn'.format(i))
        new_offset = self.rotate2d(*bike_offset)
        print(new_offset)
        new_bike_spawn = (bike_spawn_wp[0][0] + new_offset[0], bike_spawn_wp[0][1] + new_offset[1], math.radians(new_car_spawn[2]))
        new_car_spawn = list(new_car_spawn)
        new_car_spawn[2] = math.radians(new_car_spawn[2])
        new_car_spawn = tuple(new_car_spawn)

        return new_car_spawn, new_bike_spawn


if __name__ == "__main__":
    
    m = ConfigManipulator(world_name = "Town01")

#     v = [a for a in m.world.get_actors() if 'role_name' in a.attributes.keys() and a.attributes['role_name'] == 'hero'][0]
#     b = [a for a in m.world.get_actors() if 'role_name' in a.attributes.keys() and a.attributes['role_name'] == 'adversary'][0]

#     wpv = m.world.get_map().get_waypoint(v.get_location())
#     ptb = b.get_transform()
#     wpb = m.world.get_map().get_waypoint(b.get_location())

#     wp = [a for a in list(itertools.chain(*m.world.get_map().get_topology())) if a.is_junction]

#     dists = sorted(wpv.transform.location.distance(a.transform.location) for a in wp)

    #waypoints = m.world.get_map().generate_waypoints(100)
    #for w in waypoints:
    #    m.world.debug.draw_string(w.transform.location, f'O [{w.transform.location} \n {w.transform.rotation.yaw}]', draw_shadow=False,
    #                                    color=carla.Color(r=255, g=0, b=0), life_time=1200.0,
    #                                    persistent_lines=True)
    print(m.rotate2d(1.0, 0.0, 0))
#     for i in dists:
#         if wpv.next(i)[0].is_junction:
#             print(i)
#             closest_junction = wpv.next(i)[0]
#             break

#     print('base waypoint:')
#     print(closest_junction)
#     #print([(a.transform.location.x, a.transform.location.y, a.transform.location.z) for a in wpv.next(50)])
#     print('vehicle pos:')
#     print(wpv)
#     print('bike pos:')
#     print(ptb)
#     print(wpb)

#     print('Bike distance to base')
#     print(closest_junction.transform.location.distance(wpb.transform.location))

#     print('Bike offset relative to wp')
#     bike_offset = (ptb.location.x - wpb.transform.location.x, ptb.location.y - wpb.transform.location.y, math.radians((ptb.rotation.yaw - wpb.transform.rotation.yaw)%360))
#     print(bike_offset)

#     print('')

#     bike_spawn_wp = []
#     new_car_spawn_wp_good = False

#     while len(bike_spawn_wp) == 0 or not new_car_spawn_wp_good:

#         new_junction = random.choice(wp)
#         new_wp = new_junction.previous(28.6)
#         new_yaw = [a.transform.rotation.yaw for a in new_wp][0]

#         new_car_spawn = [(a.transform.location.x, a.transform.location.y, a.transform.location.z, a.transform.rotation.yaw) for a in new_wp][0]
#         new_car_spawn_wp_good = abs(new_junction.transform.rotation.yaw - new_car_spawn[3]) < 45

#         bike_spawn_wp = [(a.transform.location.x, a.transform.location.y, a.transform.location.z, a.transform.rotation.yaw) for a in new_junction.next(closest_junction.transform.location.distance(wpb.transform.location)) if abs((a.transform.rotation.yaw - new_yaw) - (wpb.transform.rotation.yaw - wpv.transform.rotation.yaw)) < 50]
        

#     print('new junction:')
#     print(new_junction)
#     print('new car spawn:')

#     print(new_car_spawn)
#     #print([(a.transform.get_forward_vector().x, a.transform.get_forward_vector().y, a.transform.get_right_vector().x, a.transform.get_right_vector().y) for a in new_wp])

#     print([((wpv.transform.rotation.yaw) - (wpb.transform.rotation.yaw ) + 360)%360 for a in new_junction.next(closest_junction.transform.location.distance(wpb.transform.location))])

#     print('new bike spawn wp:')
#     print(bike_spawn_wp)
#     print('new bike spawn:')
#     new_offset = m.rotate2d(*bike_offset)
#     print(new_offset)
#     print((bike_spawn_wp[0][0] - new_offset[0], bike_spawn_wp[0][1] - new_offset[1]))
    


#     pass