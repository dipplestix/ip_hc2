import math
import os
from argparse import ArgumentParser
from datetime import datetime
from pathlib import Path
from config import Config
from docplex.mp.model import Model
from solver import Solver
import cProfile
import re

parser = ArgumentParser()
parser.add_argument("input_file", type=str)


def main(args):
    input_file = Path(args.input_file)
    filename = input_file.name
    solver = Solver.from_file(args.input_file)
    start_time = datetime.now()
    solution = solver.solve()
    end_time = datetime.now()
    delta = round((end_time - start_time).total_seconds() * 100) / 100

    print(
        f'{{"Instance": "{filename}", "Time": {delta}, "Result": {math.ceil(solution.objective_value)}, '
        f'"Solution": "OPT"}}'
    )


if __name__ == "__main__":
    args = parser.parse_args()
    main(args)
