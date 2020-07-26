import time
import pickle
import paramiko
from datetime import datetime
import xml.etree.ElementTree as ET

def get_gpu_infos(nvidiasmi_output):
    gpus = nvidiasmi_output.findall('gpu')

    gpu_infos = []
    for idx, gpu in enumerate(gpus):
        model = gpu.find('product_name').text
        total_memory = gpu.find('fb_memory_usage').find('total').text
        used_memory = gpu.find('fb_memory_usage').find('used').text
        gpu_util = gpu.find('utilization').find('gpu_util').text
        processes = gpu.findall('processes')[0]
        pids = [process.find('pid').text for process in processes]
        gpu_infos.append({'idx': idx, 'model': model, 'pids': pids, 'gpu_util': gpu_util,
                          'used_mem': used_memory, 'total_mem': total_memory})

    return gpu_infos

def get_users_by_pid(ps_output):
    users_by_pid = {}
    for line in ps_output.strip().split('\n'):
        pid, user = line.split()
        users_by_pid[pid] = user

    return users_by_pid

def get_program_by_pid(ps_output):
    program_by_pid = {}
    for line in ps_output.strip().split('\n'):
        line = line.split()
        program_by_pid[line[0]] = ' '.join(line[1:])

    return program_by_pid

def start_connections(server_list):
    clients = []
    servers = []
    for server in server_list:
        try:
            client = paramiko.SSHClient()
            client.load_system_host_keys()
            client.connect(server, gss_auth=True, gss_kex=True)
            clients.append(client)
            servers.append(server)
        except:
            print('Cannot connect to ', server)
    return clients, servers

def end_connections(clients):
    for client in clients:
        client.close()

def run_cmd(client, cmd):
    _, stdout, _ = client.exec_command(cmd)
    stdout = stdout.read().decode(encoding='UTF-8')
    return stdout

def get_server_info(server, client):
    gpu_infos = ET.fromstring(run_cmd(client, 'nvidia-smi -q -x'))
    gpu_infos = get_gpu_infos(gpu_infos)

    pids = [pid for gpu_info in gpu_infos for pid in gpu_info['pids']]
    if len(pids) > 0:
        PS_CMD = 'ps -o pid= -o ruser=  -p {pids}'.format(pids=','.join(pids))
        ps = run_cmd(client, PS_CMD)
        users_by_pid = get_users_by_pid(ps)
        PS_CMD = 'ps -o pid= -o args=  -p {pids}'.format(pids=','.join(pids))
        ps = run_cmd(client, PS_CMD)
        program_by_pid = get_program_by_pid(ps)
    else:
        users_by_pid = {}
        program_by_pid = {}

    results = []
    details = []
    for gpu_info in gpu_infos:
        users = set((users_by_pid[pid] for pid in gpu_info['pids']))

        if len(gpu_info['pids']) == 0:
            status = 'Free'
        else:
            used_mem = gpu_info['used_mem']
            total_mem = gpu_info['total_mem']
            gpu_util = gpu_info['gpu_util']
            status = '{} out of {} used by {} (GPU utilization: {})'.format(used_mem, total_mem,
                                    ', '.join(users), gpu_util)
            for pid in gpu_info['pids']:
                user = users_by_pid[pid]
                program = program_by_pid[pid]
                details.append((server.split('.')[0], gpu_info['idx'], user, program))

        results.append('GPU {} ({}): {}'.format(gpu_info['idx'],
                                        gpu_info['model'],
                                        status))
    return results, details

def get_servers_info(servers, clients):
    server_infos = {}
    user_infos = []
    for i in range(len(servers)):
        server = servers[i]
        client = clients[i]
        results, details = get_server_info(server, client)
        server_infos[server] = results
        user_infos += details
    return server_infos, user_infos

def gpu_monitor_server(servers, clients):
    server_info, user_infos = get_servers_info(servers, clients)

    results = []
    for server in servers:
        tmp = [server]
        try:
            tmp.append(server_info[server])
        except:
            tmp.append(["This server is down! Keep calm and email Stephen."])
        results.append(tmp)

    timestamp = time.time()
    timestamp = datetime.fromtimestamp(timestamp)

    return {'server_info' : results,
            'user_info'   : user_infos,
            'timestamp'   : timestamp}

if __name__ == '__main__':
    servers_all = ['nescafe.cs.washington.edu', 'sanka.cs.washington.edu',
                   'arabica.cs.washington.edu', 'chemex.cs.washington.edu',
                   'lungo.cs.washington.edu',   'ristretto.cs.washington.edu',
                   'latte.cs.washington.edu',   'sidamo.cs.washington.edu',
                   'caffeine.cs.washington.edu','cortado.cs.washington.edu']

    clients, servers = start_connections(servers_all)
    connect_t = time.time()
    is_connect = True
    while True:
        try:
            info = gpu_monitor_server(servers, clients)
            with open('info.pkl', 'wb') as f:
                pickle.dump(info, f)
        except Exception as e:
            print(e)
        if time.time() - connect_t > 600:
            end_connections(clients)
            clients, servers = start_connections(servers_all)
            connect_t = time.time()
        time.sleep(20)
