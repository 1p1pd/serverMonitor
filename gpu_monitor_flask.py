import pickle
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def gpu_monitor_server():
    with open('info.pkl', 'rb') as f:
        info = pickle.load(f)

    results = info['serverInfo']
    user_count = {}
    for server, status in results:
        for s in status:
            if 'used by' in s:
                username = s.split('used by')[1].split('(')[0].strip()
                try:
                    user_count[username] += 1
                except Exception as e:
                    user_count[username] = 1
    user_count = [(k, v) for k, v in user_count.items()]
    user_count.sort(key=lambda i: i[1], reverse=True)
    timestamp = info['timestamp']
    return render_template('files.html', userCount=user_count, serverInfo=results, timestamp=timestamp)
