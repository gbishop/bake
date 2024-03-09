import pulp


class Recipe:
    vars = {}
    constraints = []
    objective = 0

    def __getattr__(self, name):
        if name not in self.vars:
            self.vars[name] = pulp.LpVariable(name, 0, None)
        return self.vars[name]

    def __iadd__(self, constraint):
        self.constraints.append(constraint)
        return self


R = Recipe()
