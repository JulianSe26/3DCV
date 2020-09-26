from enum import Enum

schema_restriction_values = [
    "CloudState",
    "RouteStrategy",
    "MiscObjectCategory",
    "ObjectType",
    "PrecipitationType",
    #"VehicleCategory",
    "Rule",
    "PedestrianCategory",
    "RouteStrategy"
]

class ValTypes(str, Enum):
    CATEGORICAL = 'CATEGORICAL'
    INT = 'INT'
    DOUBLE = 'Double'
    UNKNOWN = 'UNKNOWN'

    @staticmethod
    def get_key_for_val(val):
        if val in ValTypes._value2member_map_:
            return val
        elif val in schema_restriction_values:
            return ValTypes.CATEGORICAL
        elif val == 'name':
            return ValTypes.CATEGORICAL
        else:
            return ValTypes.UNKNOWN


class GeneratorValues:

    def __init__(self, val_type:ValTypes, val=None, val_range=(None, None, None)):
        self.type = val_type
        self.val = val
        self.range = val_range

    def __str__(self):
        return 'ValType={}; val={}; val_range={}'.format(self.type, self.val, self.range)
