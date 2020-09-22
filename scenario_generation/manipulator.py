import carla
import random
from typing import List
import itertools

class ConfigManipulator:
    def __init__(self, world_name: str = "Town01", host: str = "localhost", port: int = 2000):
        self.client = carla.Client(host, port)
        #self.client.load_world(world_name)
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


if __name__ == "__main__":
    
    m = ConfigManipulator(world_name = "Town01")

    #print([a for a in m.world.get_actors() if a.type_id == 'vehicle.tesla.model3'])
    v = [a for a in m.world.get_actors() if a.type_id == 'vehicle.tesla.model3'][0]
    b = [a for a in m.world.get_actors() if a.type_id == 'vehicle.diamondback.century'][0]

    ptv = m.world.get_map().get_waypoint(v.get_location())
    ptb = b.get_transform()#m.world.get_map().get_waypoint(b.get_location())
    wpb = m.world.get_map().get_waypoint(b.get_location())

    wp = [a for a in list(itertools.chain(*m.world.get_map().get_topology())) if a.is_junction]

    dists = sorted(ptv.transform.location.distance(a.transform.location) for a in wp)

    waypoints = m.world.get_map().generate_waypoints(100)
    for w in waypoints:
        m.world.debug.draw_string(w.transform.location, f'O [{w.transform.location} \n {w.transform.rotation.yaw}]', draw_shadow=False,
                                        color=carla.Color(r=255, g=0, b=0), life_time=1200.0,
                                        persistent_lines=True)

    for i in dists:
        if ptv.next(i)[0].is_junction:
            print(i)
            next_junction = ptv.next(i)[0]
            break

    print('base waypoint:')
    print(next_junction)
    #print([(a.transform.location.x, a.transform.location.y, a.transform.location.z) for a in ptv.next(50)])
    print('vehicle pos:')
    print(ptv)
    print('bike pos:')
    print(ptb)
    print(wpb)

    print('Bike distance to base')
    print(next_junction.transform.location.distance(wpb.transform.location))

    print('Bike offset')
    print()

    print('')



    new_junction = random.choice(wp)
    new_wp = new_junction.previous(28.6)


    print('new junction:')
    print(new_junction)
    print('new car spawn:')
    print([(a.transform.location.x, a.transform.location.y, a.transform.location.z, a.transform.rotation.yaw) for a in new_wp])
    #print([(a.transform.get_forward_vector().x, a.transform.get_forward_vector().y, a.transform.get_right_vector().x, a.transform.get_right_vector().y) for a in new_wp])

    new_yaw = [a.transform.rotation.yaw for a in new_wp][0]

    print([((ptv.transform.rotation.yaw) - (wpb.transform.rotation.yaw ) + 360)%360 for a in new_junction.next(next_junction.transform.location.distance(wpb.transform.location))])

    print('new bike spawn:')
    print([(a.transform.location.x, a.transform.location.y, a.transform.location.z, a.transform.rotation.yaw) for a in new_junction.next(next_junction.transform.location.distance(wpb.transform.location)) if (a.transform.rotation.yaw - new_yaw) - (wpb.transform.rotation.yaw - ptv.transform.rotation.yaw) < abs(90)])
    


    pass