from enum import Enum


class OutputFormat(str, Enum):
    json = "json"
    junit = "junit"
