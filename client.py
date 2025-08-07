import socket
import threading
import time
import tempfile
import queue
import os
import keyboard
import render_funcs
import ctypes
import msvcrt
import re

vlc_path = r'C:\Program Files\VideoLAN\VLC'
os.environ['PATH'] = vlc_path + os.pathsep + os.environ['PATH']
ctypes.CDLL(os.path.join(vlc_path, "libvlc.dll"))
import vlc



instance = vlc.Instance()
player = instance.media_player_new()

HOST = '192.168.100.19'
VIDEO_PORT = 1337
AUDIO_PORT = 1338

BUFFER_SIZE = 300
MAX_QUEUE_SIZE = 600

frame_queue = queue.Queue(maxsize=MAX_QUEUE_SIZE)

current_fps = 24
fps_lock = threading.Lock()
running = True
paused = False

clear = 'cls' if os.name == 'nt' else 'clear'

ANSI_ESCAPE = re.compile(r'\x1b\[.*?m')

def clear_console_input_buffer():
    while msvcrt.kbhit():
        msvcrt.getch()

def recv_all(sock, n):
    data = b''
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data += packet
    return data

def input_listener():
    global paused, running

    while running:
        try:
            if keyboard.is_pressed('p'):
                paused = True
                player.pause()
                time.sleep(0.5)
            elif keyboard.is_pressed('r'):
                paused = False
                player.play()
                time.sleep(0.5)
            elif keyboard.is_pressed('esc'):
                running = False
                player.stop()
                break
        except:
            break
    keyboard.unhook_all()

def download_audio(audio_path, ready_event):
    print(f"connecting audio at {HOST}:{AUDIO_PORT}...")
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, AUDIO_PORT))
        print('collecting audio')
        with open(audio_path, 'wb') as f:
            while True:
                chunk = s.recv(1024)
                if not chunk:
                    break
                f.write(chunk)
    print('audio loaded')
    ready_event.set()

def video_receiver(fps_holder, ready_event):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        print(f"connecting video at {HOST}:{VIDEO_PORT}...")
        s.connect((HOST, VIDEO_PORT))
        print('video connection established')

        t0 = time.time()
        for _ in range(BUFFER_SIZE):
            size_bytes = recv_all(s, 4)
            if not size_bytes:
                return
            size = int.from_bytes(size_bytes, 'big')
            frame_data = recv_all(s, size)
            frame = frame_data.decode('utf-8')
            frame_queue.put(frame)
        fps = BUFFER_SIZE / (time.time() - t0)
        fps_holder.append(fps)
        print(f"buffer loaded. fps: {fps:.2f}")
        ready_event.set()
        os.system(clear)

        try:
            while running:
                size_bytes = recv_all(s, 4)
                if not size_bytes:
                    break
                size = int.from_bytes(size_bytes, 'big')
                frame_data = recv_all(s, size)
                if frame_data is None:
                    break
                frame = frame_data.decode('utf-8')

                while frame_queue.full() and running:
                    try:
                        frame_queue.get_nowait()
                    except queue.Empty:
                        break
                frame_queue.put(frame)
        except Exception as e:
            print('got an error while getting the video: ', e)

def video_player(start_event, fps):
    global running, paused
    frame_index = 0
    paused_start_time = None
    accumulated_pause_time = 0

    start_event.wait()
    start_time = time.time()

    while running:
        if paused:
            if paused_start_time is None:
                paused_start_time = time.time()
            time.sleep(0.1)
            continue
        else:
            if paused_start_time is not None:
                accumulated_pause_time += time.time() - paused_start_time
                paused_start_time = None

        adjusted_start_time = start_time + accumulated_pause_time

        target_time = adjusted_start_time + frame_index / fps
        delay = max(0, target_time - time.time())
        time.sleep(delay)

        if not frame_queue.empty():
            frame = frame_queue.get()
            framed = add_frame_to_ascii(frame)
            render_funcs.render_frame(framed)

        frame_index += 1

def on_end_reached(event):
    global running
    running = False

def visible_len(s):
    return len(ANSI_ESCAPE.sub('', s))

def add_frame_to_ascii(frame: str) -> str:
    lines = frame.split('\n')

    while lines and lines[-1].strip() == '':
        lines.pop()

    max_width = max(visible_len(line) for line in lines) if lines else 0

    top_border = "+" + "-" * max_width + "+"
    bottom_border = top_border

    framed_lines = [top_border]
    for line in lines:
        line_visible_len = visible_len(line)
        padding = max_width - line_visible_len
        framed_line = "|" + line + " " * padding + "|"
        framed_lines.append(framed_line)
    framed_lines.append(bottom_border)

    return "\n".join(framed_lines)


def main():
    os.system(clear)

    audio_ready = threading.Event()
    video_ready = threading.Event()
    start_event = threading.Event()
    fps_holder = []

    audio_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3").name

    threading.Thread(target=input_listener, daemon=True).start()
    threading.Thread(target=download_audio, args=(audio_file, audio_ready), daemon=True).start()
    threading.Thread(target=video_receiver, args=(fps_holder, video_ready), daemon=True).start()

    audio_ready.wait()
    video_ready.wait()

    media = instance.media_new(audio_file)
    player.set_media(media)

    event_manager = player.event_manager()
    event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, on_end_reached)

    fps = fps_holder[0]
    threading.Thread(target=video_player, args=(start_event, fps), daemon=True).start()

    player.play()
    start_event.set()

    try:
        while running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass

    while msvcrt.kbhit():
        msvcrt.getch()

    os.remove(audio_file)
    os.system(clear)

if __name__ == "__main__":
    main()
