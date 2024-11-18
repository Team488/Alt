import socket
import cv2
import threading
import numpy as np

def handle_client(client_socket, client_address):
    """Handles incoming messages from a client (streaming video frames)."""
    print(f"Connection established with {client_address}")
    data = b''  # Initialize an empty byte string to accumulate the image data
    try:
        while True:
            chunk = client_socket.recv(10000)
            if not chunk:
                break  # Connection closed by client
            data += chunk  # Append the chunk to the data buffer
            
            # Try to find a complete frame based on markers
            while len(data) > 0:
                start_idx = data.find(b'\xff\xd8')  # JPEG start marker
                end_idx = data.find(b'\xff\xd9')    # JPEG end marker
                
                if start_idx != -1 and end_idx != -1:
                    # We have a complete image
                    # end_idx += 2  # Include the JPEG end marker
                    frame_data = data[start_idx:end_idx]
                    print(f"Start{start_idx} End {end_idx}")
                    print(f"Length of full data {len(data)}")
                    print(f"Length of frame data {len(frame_data)}")
                    data = data[end_idx+2:]  # Remove the processed image data
                    
                    # Convert byte data to NumPy array
                    nparr = np.frombuffer(frame_data, np.uint8)
                    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                    
                    if img is not None:
                        cv2.imshow(f"Received Image from {client_address}", img)
                        cv2.waitKey(1)
                    else:
                        print(f"Failed to decode image from {client_address}")
                else:
                    break  # Wait for more data
    except Exception as e:
        print(f"Error handling client {client_address}: {e}")
    finally:
        client_socket.close()
        print(f"Connection closed with {client_address}")
        cv2.destroyAllWindows()

def start_server(host='localhost', ports=[5000, 5001, 5002, 5003, 5004]):
    """Starts the server and listens on multiple ports."""
    # Create a server socket for each port
    threads = []
    for port in ports:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind((host, port))
        server_socket.listen(1)
        print(f"Server listening on port {port}...")

        # Accept client connections and start a thread for each one
        def listen_on_port(server_socket):
            while True:
                client_socket, client_address = server_socket.accept()
                # Start a new thread to handle the client connection
                client_thread = threading.Thread(target=handle_client, args=(client_socket, client_address))
                client_thread.start()
                threads.append(client_thread)

        # Start a separate thread to handle connections for this port
        port_thread = threading.Thread(target=listen_on_port, args=(server_socket,))
        port_thread.start()
        threads.append(port_thread)

    # Wait for all threads to finish
    for thread in threads:
        thread.join()

# Run the server
start_server()
