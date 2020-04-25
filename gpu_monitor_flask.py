import pickle
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def gpu_monitor_server():
    with open('info.pkl', 'rb') as f:
        info = pickle.load(f)

    results = info['serverInfo']
    users = []
    user_server = {}
    user_util = {}
    for server, status in results:
        server = server.split('.')[0]
        for s in status:
            if 'used by' in s:
                usernames = s.split('used by')[1].split('(')[0].strip()
                usernames = usernames.split(', ')
                util = int(s.split('GPU utilization:')[1].split()[0])
                for username in usernames:
                    try:
                        user_server[(username, server)] += 1
                    except Exception as e:
                        user_server[(username, server)] = 1
                    try:
                        user_util[username] += [util]
                    except:
                        user_util[username] = [util]
                    if username not in users:
                        users += [username]

    user_server = [(k1, k2, v) for (k1, k2), v in user_server.items()]
    user_count = {}
    for user in users:
        util = user_util[user]
        user_count[user] = [0, '{:.2f} % utilization'.format(sum(util) / len(util)), []]

    for user in users:
        for username, servername, n_gpu in user_server:
            if user == username:
                user_count[username][0] += n_gpu
                user_count[username][2] += ['{} * {}'.format(servername, n_gpu)]

    user_count = [(k, n, u, ', '.join(v)) for k, [n, u, v] in user_count.items()]
    user_count.sort(key=lambda i: i[1], reverse=True)

    timestamp = info['timestamp']
    return render_template('files.html', userCount=user_count, serverInfo=results, timestamp=timestamp)
