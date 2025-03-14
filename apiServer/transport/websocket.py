
import queue
import threading
from websockets.sync.server import serve
from apiServer.detection import detect
message_queue = queue.Queue()
from logger import logger as LOGGER
 
websocket_map = {}
websocket_map_normal_key = "normal"


def push_msg(id, msg):
    message_queue.put({"id": id, "msg": msg})

def websocket_handler(websocket):
    
    path_str = websocket.request.path
    # print(f"websocket path: {path_str}")
    path_array = path_str.split("/")
    device_id=""
    if len(path_array) == 2:
        device_id = path_array[1]
        detect_instance = detect.get_detection(device_id)
        if detect_instance is not None:
            detect_instance.is_detect=True
    elif len(path_array) == 3:
        device_id = path_array[2]
        detect_instance = detect.get_detection(device_id)
        if detect_instance is not None:
            if path_array[1] == "raw":
                detect_instance.is_detect=False
            else:
                detect_instance.is_detect=True
    else:
        device_id = websocket_map_normal_key
    if device_id not in websocket_map:
        websocket_map[device_id] = set()
   
    websocket_map[device_id].add(websocket)
    try:
        while True:
            message = websocket.recv()
            # print(message)
            if message == "closed":
                websocket_map[device_id].remove(websocket)
                break
    except Exception as e:
        LOGGER.error(f"websocket closed path: {device_id}, exception: {e}")
 
def broadcast_messages():
    while True:
        try:
            message = message_queue.get(timeout=5)
            # print(message)
            if message is None:
                break
            if("id" in message):
                id = message.get("id", None)
                msg = message.get("msg", "")
                if id is not None:
                    websocket_connections = websocket_map.get(id, None) 
                    if websocket_connections:
                        for ws in list(websocket_connections):  
                            try:
                                # print(f"send msg by websocket:{id}")
                                ws.send(msg)
                            except Exception as e:
                                LOGGER.error(f"Failed to send message to {id}, exception: {e}")
                                websocket_connections.remove(ws)
        except queue.Empty:
            continue
        except Exception:
            continue

def start_server():
    port = 8765
    with serve(websocket_handler, "0.0.0.0", port, close_timeout=60) as server:
        LOGGER.info(f"start websocket server successful :{port}")
        server.serve_forever()

def run_server():
    websocket_thread = threading.Thread(target=start_server)
    websocket_thread.setDaemon(True)
    websocket_thread.start()

    thread_count = 5
    for i in range(thread_count):
        broadcast_thread = threading.Thread(target=broadcast_messages) 
        broadcast_thread.daemon = True 
        broadcast_thread.start() 
 
