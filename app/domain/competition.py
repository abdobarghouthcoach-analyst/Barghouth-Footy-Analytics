from enum import Enum


class CompetitionType(str, Enum):
    LEAGUE = "league"
    CUP = "cup"
    INTERNATIONAL = "international"


class CompetitionLevel(str, Enum):
    FIRST = "first"
    SECOND = "second"
    YOUTH = "youth"
