from __future__ import annotations
from typing import List
from dataclasses import dataclass
import random
import numpy as np
from docplex.mp.model import *
from docplex.mp.solution import SolveSolution
from docplex.mp.solution import SolveSolution
from datetime import datetime
from config import Config
import math
import heapq as hq
from numba import jit


@dataclass
class Solution:
    objective_value: float


def check_integer(solution) -> bool:
    eps = 1e-5
    all_ints = True
    for val in solution.get_all_values():
        if abs(val - round(val)) > eps:
            all_ints = False
            break
        #     if abs(val - round(val)) > diff_val:
        #         diff_val = abs(val - round(val))
        #         max_cons = i
        #         best_val = round(val)
        # i += 1

    # return all_ints, max_cons, best_val
    return all_ints


class Solver:
    def __init__(self, config: Config):
        self.config = config
        self.model = Model()
        self.build_lp()
        self.h = []
        self.current = None
        self.best = None
        self.counter = 0
        self.branching = 'best'

    def build_lp(self):
        n_t = self.config.n_tests
        n_d = self.config.n_diseases
        A = self.config.tests_for

        # set up variables
        # Which tests to use
        self.use = [self.model.continuous_var(0, 1, f'use_{n}') for n in range(n_t)]
        # These variables represent for any given pair (j, k) if j is tested without k at least once.
        more_than_idx = [(j, k) for j in range(n_d) for k in range(n_d)]
        self.more_than = self.model.continuous_var_dict(more_than_idx, 0, 1, 'ge')
        # This will find which disease we don't test for
        self.check = [self.model.continuous_var(0, 1, f'check_{n}') for n in range(n_d)]

        # Set up constraints
        # There is one disease we don't need to test for. If everything shoes up negative, they have that one
        self.model.add_constraint(sum(self.check) == 1)
        for i in range(n_t):
            # We don't use tests that test for all diseases. This constraint shouldn't be needed, but just in case.
            if sum([A[i][j] for j in range(n_d)]) == n_d:
                self.model.add_constraint(self.use[i] == 0)
        for j in range(n_d):
            # Each disease (except for the one in self.check) must be tested for at least once
            n_tested = sum([A[i][j]*self.use[i] for i in range(n_t)])
            self.model.add_constraint(n_tested >= 1 - self.check[j])
            # checked = self.model.sum([self.check[j]*self.more_than[(j, k)] for k in range(n_d)])
            # self.model.add_constraint(checked == 0)
            # # self.model.add_constraint(n_tested>=1)
            # Each member of a pair must be tested for without the other member at least once
            for k in range(n_d):
                if j > k:
                    # One is allowed to be tested an equal number of times that the pair is tested, but the other must
                    # be tested more
                    self.model.add_constraint(self.more_than[(j, k)] + self.more_than[(k, j)] == 1)
                if j != k:
                    num_tested_as_pair = self.model.sum([A[i][j]*A[i][k]*self.use[i] for i in range(n_t)])
                    num_tested_alone = self.model.sum([self.use[i]*A[i][j] for i in range(n_t)])
                    diff = num_tested_alone - num_tested_as_pair
                    self.model.add_constraint(diff >= self.more_than[(j, k)])
                if j == k:
                    self.model.add_constraint(self.more_than[(j, k)] == 0)

        # Cost to use the tests
        self.objective = self.model.scal_prod(self.use, self.config.cost_t)

    def get_next(self, solution):
        names = [f'use_{n}' for n in range(self.config.n_tests)]
        vals = [abs(solution.get_value(i) - round(solution.get_value(i))) for i in names]
        if max(vals) != 0:
            index = vals.index(max(vals))
        else:
            names = [f'check_{n}' for n in range(self.config.n_diseases)]
            vals = [abs(solution.get_value(i) - round(solution.get_value(i))) for i in names]
            if max(vals) != 0:
                index = vals.index(max(vals))
            else:
                names = [f'ge_{i}_{j}' for i in range(self.config.n_diseases) for j in range(self.config.n_diseases)
                         if solution.get_value(f'ge_{i}_{j}')<1]
                vals = [abs(solution.get_value(i) - round(solution.get_value(i))) for i in names]
                index = vals.index(max(vals))
        return names[index]

    def branch(self, var, constraints):
        var = self.model.get_var_by_name(var)
        # print(f'For this round I am dealing with {var}')
        self.counter += 1
        for v in [1, 0]:
            cons = constraints[:]
            cons.append(var == v)
            hc = self.model.add_constraints(cons)
            ns = self.model.solve()
            if self.counter == 1:
                a = self.model.get_cplex()
                print("CURRENT TABLEAU:")
                print(len(a.solution.advanced.binvarow()[0]))
                print(len(ns.get_all_values()))
                print(len(a.solution.advanced.binvrow()))
                print(len(a.solution.advanced.binvarow()))

                # for row in a.solution.advanced.binvarow():
                #     print(row)
            if ns:
                is_int = check_integer(ns)
                if self.best is None and is_int:
                    # print(f'I have an integer soluition: {var}, {ns.objective_value}')
                    self.best = ns
                elif is_int:
                    # print(f'I have an integer soluition: {var}, {ns.objective_value}')
                    if math.floor(ns.objective_value) <= math.floor(self.best.objective_value):
                        self.best = ns
                else:
                    # print(f'I am adding {var} == {v} to the heap with value {ns.objective_value}')
                    # hq.heappush(self.h, (ns.objective_value + random.random()/1000, [cons, next_var]))
                    next_var = self.get_next(ns)
                    if self.best is None:
                        if self.branching == 'dfs':
                            self.h.append((ns.objective_value, [cons, next_var]))
                        if self.branching == 'best':
                            hq.heappush(self.h, (ns.objective_value + random.random()/1000, [cons, next_var]))
                    elif math.floor(ns.objective_value) <= math.floor(self.best.objective_value):
                        if self.branching == 'dfs':
                            self.h.append((ns.objective_value, [cons, next_var]))
                        if self.branching == 'best':
                            hq.heappush(self.h, (ns.objective_value + random.random()/1000, [cons, next_var]))

            else:
                pass
                # print('I am not feasible')
            self.model.remove_constraints(hc)

    def solve(self) -> Solution:
        self.model.minimize(self.objective)
        solution = self.model.solve()
        # print('Solve details:')
        # print(self.model.solve_details.status)
        # int_sol, start_var, next_val = check_integer(solution)
        int_sol = check_integer(solution)
        start_var = self.get_next(solution)
        # self.best = solution
        if not int_sol:
            self.branch(start_var, [])
        else:
            self.best = solution
        while self.h:
            if self.branching == 'best':
                score, info = hq.heappop(self.h)
            if self.branching == 'dfs':
                score, info = self.h.pop(-1)
            if self.best is None:
                self.branch(info[1], info[0])
            elif math.floor(score) >= math.floor(self.best.objective_value):
                pass
                # print('My score is too high')
                # self.h = []
            else:
                # print('I am branching')
                self.branch(info[1], info[0])
        solution = self.best

        if solution is None:
            return None
        print('Disease we skip:')
        print([j for j in range(self.config.n_diseases) if solution.get_value(self.check[j]) == 1])
        print(f'Integer solution: {check_integer(solution)}')


        # list_ge = []
        # for j in range(self.config.n_diseases):
        #     ge = 0
        #     for k in range(self.config.n_diseases):
        #         ge += solution.get_value(f'ge_{j}_{k}')
        #     list_ge.append(ge)
        return Solution(solution.get_objective_value())

    @staticmethod
    def from_file(f) -> Solver:
        config = Config.load(f)
        return Solver(config)
