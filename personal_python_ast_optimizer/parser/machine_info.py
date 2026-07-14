import os

machine_dependent_functions: dict[str, int | None] = {"os.cpu_count": os.cpu_count()}
