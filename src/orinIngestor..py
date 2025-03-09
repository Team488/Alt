import time
import cv2
hostnames = ["photonvisionfrontright.local","photonvisionfrontleft.local","photonvisionback.local"]
dummyStr = "?dummy=param.mjpg"
port = 1182

captures = []
writers = []

for hostname in hostnames:
    loc = f"{hostname}/stream{dummyStr}"
    cap = cv2.VideoCapture(loc)

    captures.append(cap)

    path = f"{hostname}_{time.time()}.mp4"

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")

    w = cap.get(cv2.CAP_PROP_FRAME_WIDTH)
    h = cap.get(cv2.CAP_PROP_FRAME_HEIGHT)
    writer = cv2.VideoWriter(
        path,
        fourcc,
        cv2.get(cv2.CAP_PROP_FPS),
        (w,h),
        isColor=False,
    )

    writers.append(writer)



while len(writers > 0):
    for writer,cap in zip(writers,captures):
        ret,frame = cap.read()
        if not ret:
            writer.release()
            cap.release()
            writers.remove(writer)
            captures.remove(cap)
            print(f"Writer and cap have released, as frame ret was false")
        
        writer.write(frame)


        time.sleep(0.01)


