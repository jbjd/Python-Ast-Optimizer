import os
import sys

machine_dependent_attributes: dict[str, str] = {
    "os.name": os.name,
    "sys.byteorder": sys.byteorder,
    "sys.platform": sys.platform,
}

machine_dependent_functions: dict[str, int | None] = {"os.cpu_count": os.cpu_count()}
