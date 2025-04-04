import copy
from modutask.core.task import Charge

class SimulationMap:
    """ シミュレーションのマップ """
    def __init__(self, charge_stations: dict[str, Charge]):
        self._charge_stations = charge_stations

    @property
    def charge_stations(self) -> dict[str, Charge]:
        return self._charge_stations
    
    def __str__(self) -> str:
        return f"<Map: {len(self.charge_stations)} stations>"

    def __repr__(self) -> str:
        return (f"Map(charge_stations={self.charge_stations!r})")
    
    def __deepcopy__(self, memo):
        return SimulationMap(
            copy.deepcopy(self.charge_stations, memo),
        )