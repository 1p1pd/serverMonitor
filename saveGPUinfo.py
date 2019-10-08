import time
import pickle
from datetime import datetime
from gpu_monitor import getServerInfo

def gpu_monitor_server(serverList):
    serverInfo = getServerInfo(serverList)

    results = []
    serverNames = serverList[1:]
    for server in serverNames:
        tmp = [server]
        try:
            tmp.append(serverInfo[server])
        except:
            tmp.append(["This server is down! Keep calm and email Stephen."])
        results.append(tmp)

    timestamp = time.time()
    timestamp = datetime.fromtimestamp(timestamp)

    return {'serverInfo': results, 'timestamp': timestamp}


def saveInfo():
    serverList = ['-l', 'nescafe.cs.washington.edu', 'sanka.cs.washington.edu',
                        'arabica.cs.washington.edu', 'chemex.cs.washington.edu',
                        'lungo.cs.washington.edu', 'ristretto.cs.washington.edu']

    while True:
        info = gpu_monitor_server(serverList)
        with open('info.pkl', 'wb') as f:
            pickle.dump(info, f)
        time.sleep(60)

if __name__ == '__main__':
    saveInfo()
