# Recherche

Um den Scenario Runner unter Windows zum Laufen zu bekommen musste ich diese Zeile in der scenario_runner.py auskommentieren:
```signal.signal(signal.SIGHUP, self._signal_handler)```.

## Sonstiges

Hier ist noch ein Tutorial für Carla und Python, da wird auch mit Reinforcement Learning gearbeitet, könnte man sich ja mal anschauen: https://pythonprogramming.net/introduction-self-driving-autonomous-cars-carla-python/.

## Anpassungen im Scenario Runner

### Autotyp

Der Autotyp lässt sich ganz einfach via xml anpassen:
```<ego_vehicle x="105" y="199.1" z="0.5" yaw="0" model="vehicle.tesla.model3" />```

Um diesen für die anderen Autos anzupassen müsste man diese auch per xml pflegen, was momentan nicht überall der Fall ist (in der ```cut_in.py``` zum Beispiel aber schon). In den Szenarien ist der Typ des vorherfahrenden Autos fest gesetzt, siehe z.B. ```follow_leading_vehicle.py```:
```
first_vehicle = CarlaActorPool.request_new_actor('vehicle.nissan.patrol', first_vehicle_transform, color="0,0,255")
```

### Autofarbe

Autofarbe der anderen Autos können auch per XML angepasst werden, indem einfach ein Attribut 'color' hinzugefügt wird. 
Damit das funktioniert, muss in der Szenario .py jedoch noch folgendes angepasst werden: z.B. ```first_vehicle = CarlaActorPool.request_new_actor('vehicle.nissan.patrol', first_vehicle_transform, color="255,255,255")```

Dort wo der Actor angefordert wird, muss die Farbe hinzugefügt werden, um es per XML steuerbar zu machen, dann im besten Falle per Attribut.

Damit der Wert aus der xml auch in der vehicle_configuration ankommt, muss zudem folgendes in der init der ActorConfiguration in der scenario_configuration.py angepasst werden:
```
color = None
if 'color' in node.keys():
    color = node.attrib['color']

super(ActorConfiguration, self).__init__(node.attrib.get('model', 'vehicle.*'),
                                            carla.Transform(carla.Location(x=pos_x, y=pos_y, z=pos_z),
                                                            carla.Rotation(yaw=yaw)),
                                            node.attrib.get('rolename', rolename),
                                            autopilot, random_location, amount=amount, color=color)
```

Jetzt kann sowohl von dem ego_vehicle als auch von anderen die Farbe angepasst werden.

### Geschwindigkeit

Die Geschwindigkeit von den Actoren lässt sich auch anpassen, z.B. in dem FollowLeadingVehicle Szenario über den Parameter ```self._first_vehicle_speed = 15```


### Spawnpoint

In den Szenarien sind bereits verschiedene Varianten vorhanden (üblicherweise um die 10), die auf verscheidenen Karten sowie mit verschiedenen Spawn Points arbeiten.
Reicht das?? 

Ansonsten ist es möglich von der Karte per ```self._map.get_spawn_points()``` alle möglichen Spawn Points zu bekommen. Hier könnte dann zufällig einer ausgesucht werden.
Eventuell ist es damit umsetzbar, dass die anderen Actoren (vorausfahrendes Auto, kreuzendes Auto, Fußgänger) in der Nähe an der nächstbesten Position gespawn werden... müsste man aber nochmal genauer reinschauen.


### Wetter

Das Wetter lässt sich auch recht einfach in der XML-Konfigurations Datei anpassen und das sieht wie folgt aus:
```
<weather cloudiness="100" precipitation="100" precipitation_deposits="10" wind_intensity="0" sun_azimuth_angle="0" sun_altitude_angle="75" />
```

Beeinflusst werden kann die Bewölkung, Regenmenge, Regenmenge auf dem Boden, Windintensität, Sonnenstand.
Die Werte könnne alle zwischen 0 und 100 liegen (außer die Winkel für den Sonnenstand);:
- azimuth: zwischen 0 und 360°
- altitude: zwischen -90 und 90°

Eventuell kann man auch noch mit Nebel (fog) arbeiten, gibt es zumindes in den Carla Wetter-configs.


### weitere NPCs in der Welt

verschiedene Möglichkeiten:
- Aufruf des Carla examples ```spawn_npc.py``` in der init methode des scenario runner (so werden bei jedem ausgeführten Scenario neu NPCs in der Welt gespawnt)
- über XML
```<other_actor random_location="True" autopilot="True" model="vehicle.*" amount="50" />```
--> in der Szenario .py muss die Funktion _initialize_actors entsprechend angepasst werden:
```
for actor in config.other_actors:
    new_actors = CarlaActorPool.request_new_batch_actors(actor.model,
                                                        actor.amount,
                                                        self._map.get_spawn_points(),
                                                        hero=False,
                                                        autopilot=actor.autopilot,
                                                        random_location=actor.random_location)
    if new_actors is None:
        raise Exception("Error: Unable to add actor {} at {}".format(actor.model, actor.transform))

    for _actor in new_actors:
        self.other_actors.append(_actor)
```

Damit es läuft muss in der scenario_configuration.py folgendes angepasst werden (in Zeile 63 ff.):

```
super(ActorConfiguration, self).__init__(node.attrib.get('model', 'vehicle.*'),
                                            carla.Transform(carla.Location(x=pos_x, y=pos_y, z=pos_z),
                                                            carla.Rotation(yaw=yaw)),
                                            node.attrib.get('rolename', rolename),
                                            autopilot, random_location, amount=amount)
```

ACHTUNG: das Verhalten der Autos für das Szenarien wird dadurch eventuell beeinflusst, so fährt z.B. das vorausfahrende Auto in andere Autos hinein (hier müssen die Szenarien dann wahrscheinlich noch angepasst werden, z.B. um einen rudimentären Autopiloten erweitert werden).