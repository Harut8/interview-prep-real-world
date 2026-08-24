class ChargingStationTracker:
    def __init__(self) -> None:
        pass

    def add_station(self, station_id: str) -> None:
        raise NotImplementedError

    def report_status(self, station_id: str, timestamp: int, status: str) -> None:
        raise NotImplementedError

    def get_uptime(self, station_id: str, start: int, end: int) -> float:
        raise NotImplementedError

    def get_available_stations(self, timestamp: int) -> list[str]:
        raise NotImplementedError

    def get_fleet_uptime(self, start: int, end: int) -> float:
        raise NotImplementedError
