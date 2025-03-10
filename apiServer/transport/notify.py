import threading
import queue
import requests
import time
import os
from logger import logger as LOGGER
 
data_queue = queue.Queue()

notify_url = "http://127.0.0.1:8080"
if os.getenv("NOTIFY_URL") is not None:
    notify_url = os.getenv("NOTIFY_URL")
 
def notify():
    
    while True:
        msg = data_queue.get()
        if msg is None:
            time.sleep(10)
            continue
        try:
            # print(f"notify: {notify_url}, data: {["cmsgontent"]}")
            tp = msg.get("type", None)
            if not tp:
                continue
            response = None
            if(tp == "notify"):
                api_url = f"{notify_url}/v1/aiStudio/notify"
                body = msg.get("data",  "")
                response = requests.post(api_url, json=body)
            else:
                id = msg.get("data",  "")
                api_url = f"{notify_url}/v1/aiStudio/hearbeat/{id}"
                response = requests.post(api_url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            LOGGER.error(f"Failed to send, Error: {e}")
        data_queue.task_done()

worker = threading.Thread(target=notify)
worker.daemon = True 
worker.start()
 
def push_notify_msg(data):
    data_queue.put({"data":data, "type": "notify"})

def push_hearbeat_msg(data):
    data_queue.put({"data": data, "type": "hearbeat"})
 