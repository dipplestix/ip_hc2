import re
from dataclasses import dataclass

import numpy as np


@dataclass
class Config:
    n_tests: int  # the number of tests
    n_diseases: int  # the number of diseases
    cost_t: np.ndarray  # cost[t] is the cost of test t
    tests_for: np.ndarray  # tests_for[t][d] is 1 if test t detects disease d
    num_tested: np.ndarray  # Number of times each disease is tested

    @staticmethod
    def load(f):
        """
        Loads a file describing a problem configuration
        """

        def parse_line(line: str, num_type=float) -> list:
            if len(line) == 0:
                return []
            if line[-1] == "\n":
                line = line[:-1]
            return [num_type(c) for c in re.split("\t| ", line) if c != ""]

        values = {}

        with open(f, "r") as f:
            n_tests = parse_line(f.readline(), int)[0]
            n_diseases = parse_line(f.readline(), int)[0]
            values["n_tests"], values["n_diseases"] = n_tests, n_diseases
            costs = parse_line(f.readline(), int)
            values["cost_t"] = costs

            data = []
            for line in f.readlines():
                data.extend(parse_line(line, int))
            data = iter(data)
            values["tests_for"] = np.zeros([n_tests, n_diseases])
            values["num_tested"] = np.zeros(n_diseases)
            for t in range(values["n_tests"]):
                for d in range(values["n_diseases"]):
                    val = next(data)
                    values["tests_for"][t, d] = val
                    values["num_tested"][d] += val

        return Config(**values)
