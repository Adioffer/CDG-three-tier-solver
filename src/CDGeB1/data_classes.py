import dataclasses
from enum import StrEnum, auto
from typing import Optional


class Continent(StrEnum):
    AS = "Asia",  # Asia
    EU = "Europe",  # Europe
    AMN = "N. America",  # North America
    AMS = "S. America",  # South America
    AU = "Australia",  # Australia (Oceania)


@dataclasses.dataclass(frozen=True)
class CdgebEntity:
    # def __init__(self, **kwargs):
    #     names = set([f.name for f in dataclasses.fields(self)])
    #     for k, v in kwargs.items():
    #         if k in names:
    #             setattr(self, k, v)
    pass


@dataclasses.dataclass(frozen=True)
class DataCenter:
    name: str
    coordinates: tuple[float, float]  # lat, lon
    continent: Continent


@dataclasses.dataclass(frozen=True)
class FrontEnd(CdgebEntity):
    name: str
    datacenter: DataCenter

    @property
    def coordinates(self):
        return self.datacenter.coordinates

    @property
    def continent(self):
        return self.datacenter.continent


@dataclasses.dataclass(frozen=True)
class DataFile(CdgebEntity):
    name: str
    datacenter: Optional[DataCenter] = None

    @property
    def coordinates(self):
        return self.datacenter.coordinates

    @property
    def continent(self):
        return self.datacenter.continent


@dataclasses.dataclass(frozen=True)
class ProbeClient(CdgebEntity):
    name: str
    coordinates: tuple[float, float]  # lat, lon
    continent: Continent
