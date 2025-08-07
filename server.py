import socket
import threading
import time

HOST = '0.0.0.0'
VIDEO_PORT = 1337
AUDIO_PORT = 1338

path = 'video'

video_file = path+'/video.txt'
audio_file = path+'/audio.mp3'
fps_file = path+'/fps.txt'

frames = open(video_file, 'r', encoding='utf-8').read().split('qwerty')
fps = float(open(fps_file, 'r').read())

def handle_video(conn):
    print('video: client connected')
    try:
        for frame in frames:
            encoded = frame.encode('utf-8')
            size = len(encoded).to_bytes(4, 'big')
            conn.sendall(size + encoded)
            time.sleep(1 / fps)
    except BrokenPipeError:
        print('client disconnected')
    conn.close()
    print('video-stream finished')

def handle_audio(conn):
    print('audio: client connected')
    with open(audio_file, 'rb') as f:
        while chunk := f.read(1024):
            try:
                conn.sendall(chunk)
            except BrokenPipeError:
                break
    conn.close()
    print('audio-stream finished')

def start_server(port, handler):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, port))
        s.listen(1)
        print(f"waiting for connecton at {HOST}:{port}...")
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handler, args=(conn,), daemon=True).start()

if __name__ == "__main__":
    threading.Thread(target=start_server, args=(VIDEO_PORT, handle_video), daemon=True).start()
    threading.Thread(target=start_server, args=(AUDIO_PORT, handle_audio), daemon=True).start()

    input("server set up. click enter to leave...\n")

