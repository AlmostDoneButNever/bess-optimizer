from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
import os
import pandas as pd
from pyomo.environ import *

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.secret_key = 'supersecretkey'

if not os.path.exists('uploads'):
    os.makedirs('uploads')

@app.route('/')
def index():
    return render_template('input.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        return redirect(url_for('solve', filename=filename))

@app.route('/solve/<filename>')
def solve(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    df = pd.read_excel(file_path)
    
    # Example Pyomo model
    model = ConcreteModel()
    model.x = Var(initialize=1.0)
    model.obj = Objective(expr=model.x*2)

    solver = SolverFactory('glpk')
    results = solver.solve(model, tee=True)

    solution = model.x()
    
    return render_template('output.html', solution=solution)

import time

# @app.route('/solve/<filename>')
# def solve(filename):
#     file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
#     df = pd.read_excel(file_path)
    
#     # Example Pyomo model
#     model = ConcreteModel()
#     model.x = Var(initialize=1.0)
#     model.obj = Objective(expr=model.x**2)

#     # Simulate solving process
#     time.sleep(5)  # Simulating a delay for the solving process
    
#     solver = SolverFactory('glpk')
#     results = solver.solve(model)

#     solution = model.x()
    
#     return render_template('output.html', solution=solution)


if __name__ == '__main__':
    app.run(debug=True)
