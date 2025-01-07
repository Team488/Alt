import zmq
import threading

def handle_buffer(idx):
    context = zmq.Context()
    socket = context.socket(zmq.PULL)
    ipc_path = f"ipc:///tmp/python_ipc_{idx}"  # Matches TypeScript's connectionId
    socket.bind(ipc_path)

    print(f"Python listener {idx} is ready at {ipc_path}")
    while True:
        jpeg_data = socket.recv()  # Receive buffer
        with open(f"received_{idx}.jpg", "wb") as f:
            f.write(jpeg_data)
        print(f"Buffer {idx} saved as 'received_{idx}.jpg'")

# Start multiple listeners for n buffers
n = 3  # Number of buffers
threads = []
for i in range(n):
    thread = threading.Thread(target=handle_buffer, args=(i,))
    thread.start()
    threads.append(thread)

# Join threads (optional, for clean termination)
for thread in threads:
    thread.join()
