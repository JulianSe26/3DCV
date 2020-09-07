import carla
import random

client = carla.Client("localhost", 2000)

client.load_world("Town01")

class ConfigManipulator:
    def __init__(self, world_name: str = "Town01", host: str = "localhost", port: int = 2000):
        self.client = carla.Client(host, port)
        self.client.load_world(world_name)


    def get_pos_in_distance(self, x:int, y:int, z:int, distance:float) -> carla.Waypoint:
        """Get a new `carla.Waypoint` at a set distance from the current location. 
        Returned waypoints are guaranteed to be on the same road and lane.
        """
        m = client.get_world().get_map()

        s = m.get_waypoint(carla.Location(x=x, y=y, z=z)).previous(distance)

        if len(s) > 0:
            return s[0]

    def get_random_actor(self, filter:str='*') -> str:
        """Get the name of a random actor. Filter can be used to only select certain categories.
        `vehicle` for cars only, `static` for props, `walker` for people
        Default is `*`
        """
        return random.choice([bp.id for bp in client.get_world().get_blueprint_library().filter(filter)])

    def get_random_car_actor(self) -> str:
        """Wrapper around `get_random_actor` that returns the string for an available vehicle
        """
        return self.get_random_actor('vehicle')

m = ConfigManipulator()

print(m.get_random_car_actor())
