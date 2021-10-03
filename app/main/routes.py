from . import main, config
from flask import session, redirect, url_for, render_template, request, current_app
import os
from .. import socketio
from werkzeug import secure_filename
import pandas as pd
import csv


@main.route('/', methods=['GET', 'POST'])
def index():
    return render_template('brewery.html')

@main.route('/upload', methods = ['POST', 'GET'])
def upload():
    if request.method == 'POST':
        for j in request.files.keys():
            print(j)
        try:
            f = request.files['File']
            filename = secure_filename(f.filename)
            f.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            file_CSV = open(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            data_CSV = csv.reader(file_CSV)
            config.tasks = list(data_CSV)
            config.load_tasks=True
        except:
            print('no tasks yet')
    return redirect(url_for('main.index'))