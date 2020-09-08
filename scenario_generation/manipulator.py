import carla
import random

#client = carla.Client("localhost", 2000)

#client.load_world("Town07")

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

    def get_random_actor(self, filter:str='*') -> str:
        """Get the name of a random actor. Filter can be used to only select certain categories.
        `vehicle` for cars only, `static` for props, `walker` for people
        Default is `*`
        """
        return random.choice([bp.id for bp in self.client.get_world().get_blueprint_library().filter(filter)])

    def get_random_vehicle_actor(self, wheels:int=4) -> str:
        """Returns string for a vehicle with `wheels` many wheels
        """
        return random.choice([a.id for a in self.world.get_blueprint_library().filter('vehicle') if a.get_attribute('number_of_wheels').as_int() == wheels])

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

m = ConfigManipulator(world_name = "Town01")

print(m.get_random_actor('vehicle'))
