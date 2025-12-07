import os
import sys

machine_dependent_attributes: dict[str, str] = {"sys.byteorder": sys.byteorder}

machine_dependent_functions: dict[str, int | None] = {"os.cpu_count": os.cpu_count()}
