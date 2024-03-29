import os
import pickle
from flask import Flask, Markup, render_template, send_from_directory

app = Flask(__name__)

def add_color(info, top_user):
    # user_count[user] = [0,
    #                     '{:.2f}% utilization'.format(util),
    #                     []]
    k, n, u, v = info
    first, second, third = top_user
    k = Markup('<a href="{}">{}</a>'.format(k, k))
    if n == first:
        t = Markup('&#129351;')
    elif n == second:
        t = Markup('&#129352;')
    elif n == third:
        t = Markup('&#129353;')
    else:
        t = Markup('')

    if n > 8:
        n = Markup('<red>{} GPUs</red>'.format(n))
    elif n <= 8 and n > 4:
        n = Markup('<yellow>{} GPUs</yellow>'.format(n))
    elif n <= 4 and n > 1:
        n = Markup('{} GPUs'.format(n))
    else:
        n = Markup('{} GPU'.format(n))

    if u > 80:
        u = Markup('{:.2f}% utilization'.format(u))
    elif u <= 80 and u > 40:
        u = Markup('<yellow>{:.2f}%</yellow> utilization'.format(u))
    else:
        u = Markup('<red>{:.2f}%</red> utilization'.format(u))

    return (t, k, n, u, v)


def top3(arr):
    third = first = second = 0
    for i in range(len(arr)):
        if arr[i] > first:
            third = second
            second = first
            first = arr[i]
        elif arr[i] > second and arr[i] < first:
            third = second
            second = arr[i]
        elif arr[i] > third and arr[i] < second:
            third = arr[i]
    return (first, second, third)


@app.route('/')
def gpu_monitor_server():
    with open('/tmp/info.pkl', 'rb') as f:
        info = pickle.load(f)

    results = info['server_info']
    users = []
    user_server = {}
    user_util = {}
    is_conflict = False
    conflicts = []
    free_gpus = {}
    for server, status in results:
        server = server.split('.')[0]
        for s in status:
            if 'used by' in s:
                usernames = s.split('used by')[1].split('(')[0].strip()
                usernames = usernames.split(', ')
                util = int(s.split('GPU utilization:')[1].split()[0])
                if len(usernames) > 1:
                    is_conflict = True
                    conflict = ', '.join(usernames)
                    conflict = '{} on {} GPU {}'.format(conflict, server, s.split()[1])
                    conflicts.append(conflict)
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
            elif 'Free' in s:
                try:
                    free_gpus[server] += 1
                except:
                    free_gpus[server] = 1

    free_gpus = ['{} * {}'.format(s, n) for s, n in free_gpus.items()]
    if free_gpus == []:
        free_gpu_result = 'None'
    else:
        free_gpu_result = ', '.join(free_gpus)

    user_server = [(k1, k2, v) for (k1, k2), v in user_server.items()]
    user_count = {}
    for user in users:
        user_count[user] = [0, sum(user_util[user]) / len(user_util[user]), []]

    for user in users:
        for username, servername, n_gpu in user_server:
            if user == username:
                user_count[username][0] += n_gpu
                user_count[username][2] += ['{} * {}'.format(servername, n_gpu)]

    user_count = [[k, n, u, ', '.join(v)] for k, [n, u, v] in user_count.items()]
    user_count.sort(key=lambda i: i[1], reverse=True)
    top_user = top3([i[1] for i in user_count])
    user_count = [add_color(i, top_user) for i in user_count]

    timestamp = info['timestamp']
    return render_template('files.html', userCount=user_count,
                                         conflicts=(is_conflict, conflicts),
                                         freeGPU=free_gpu_result,
                                         serverInfo=results,
                                         timestamp=timestamp)

@app.route('/<username>')
def get_user_info(username):
    with open('/tmp/info.pkl', 'rb') as f:
        info = pickle.load(f)

    results = []
    user_info = [i for i in info['user_info'] if i[2] == username]
    for server, gpu_id, _, program in user_info:
        status = ('{} GPU {}:'.format(server, gpu_id), program)
        results.append(status)

    timestamp = info['timestamp']
    return render_template('user.html', username=username,
                                        user_info=results,
                                        timestamp=timestamp)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'templates'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')
