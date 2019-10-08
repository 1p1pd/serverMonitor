import pickle
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def gpu_monitor_server():
    with open('info.pkl', 'rb') as f:
        info = pickle.load(f)

    results = info['serverInfo']
    timestamp = info['timestamp']
    return render_template('files.html', serverInfo=results, timestamp=timestamp)
