from pyomo.environ import *

model = ConcreteModel()
model.x = Var(initialize=1.0)
model.obj = Objective(expr=model.x*2)

solver = SolverFactory('glpk')
results = solver.solve(model, tee=True)

solution = model.x()

print('result: ', solution)