def get_next(self, solution):
    names = [f'check_{n}' for n in range(self.config.n_diseases)]
    vals = [solution.get_value(i) for i in names]
    if max(vals) != 1:
        index = vals.index(max(vals))
        name = names[index]
    else:
        names = [f'use_{n}' for n in range(self.config.n_tests)]
        vals = [abs(solution.get_value(i) - round(solution.get_value(i))) for i in names]
        if max(vals) != 0:
            index = vals.index(max(vals))
            name = names[index]
        else:
            names = [f'ge_{i}_{j}' for i in range(self.config.n_diseases) for j in range(self.config.n_diseases)
                     if solution.get_value(f'ge_{i}_{j}')<1]
            vals = [abs(solution.get_value(i) - round(solution.get_value(i))) for i in names]
            index = vals.index(max(vals))
            name = names[index]
    return name
