#!/bin/bash
python3 saveGPUinfo.py &
sleep 10
export FLASK_APP=$(pwd)/gpu_monitor_flask.py
flask run --host=0.0.0.0 --port=9527
