from dataclasses import dataclass

@dataclass
class ChargeStation:
    name: str
    coordinate: tuple[float, float]
    charging_speed: float

class Map:
    """ シミュレーションのマップ """
    def __init__(self, charge_stations: dict[str, ChargeStation]):
        self._charge_stations = charge_stations

    @property
    def charge_stations(self) -> dict[str, ChargeStation]:
        return self._charge_stations
    
    def __str__(self):
        return f"<Map: {len(self.charge_stations)} stations>"

    def __repr__(self):
        return (f"Map(charge_stations={self.charge_stations!r})")