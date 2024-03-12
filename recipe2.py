import pulp


class Recipe:
    vars = {}
    constraints = []
    objective = 0

    def __getattr__(self, name):
        if name not in self.vars:
            self.vars[name] = pulp.LpVariable(name, 0, None)
        return self.vars[name]

    def __getitem__(self, name):
        if name.startswith("*"):
            return [self.vars[var] for var in self.vars if var.endswith(name[1:])]
        if name not in self.vars:
            self.vars[name] = pulp.LpVariable(name, 0, None)
        return self.vars[name]

    def __iadd__(self, constraint):
        if isinstance(constraint, (tuple, list)):
            for c in constraint:
                self.constraints.append(c)
        else:
            self.constraints.append(constraint)
        return self


R = Recipe()
