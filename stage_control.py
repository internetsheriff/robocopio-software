import serial
import serial.tools.list_ports
import concurrent.futures
import time


def send_xy(x, y, max_retries=3):
    msg = f"\x02{x},{y}\x03".encode()

    for attempt in range(max_retries):
        ser.write(msg)
        print(f"Sent: {msg}")
        time.sleep(1)
        response = ser.readline().strip()
        if response == b'ACK':
            print("✅ Command acknowledged")
            return True
        else:
            print(f"⚠️ Attempt {attempt+1} failed. Response: {response}")
    print("❌ Failed to get ACK from ESP32.")
    return False

def wait_until_ready():
    while True:
        ser.write(b'STATUS?\n')
        status = ser.readline().strip()
        if status == b'READY':
            print("✅ Controller is ready")
            return
        elif status == b'BUSY':
            print("⏳ Still moving...")
        else:
            print(f"⚠️ Unexpected: {status}")
        time.sleep(0.2)


def move_stage(app):
    idx = 0 
    for movement in movements_list: 
        #send_xy(movement[0]/meters_per_step_x,  movement[1]/meters_per_step_y);
        #wait_until_ready()
        if movement[3] == "STOP":
            pause_event.clear()
            app.window.after(0, app.ask_confirmation)  # Ask in main thread
            pause_event.wait()  # Wait for confirmation
        ret, frame = cap.read()
        cv2.imwrite(f'{experiment_folder}/{movement[2]}.png', frame)
        print(f'Image saved: {experiment_folder}/{movement[2]}')
        idx += 1

    print('DONE')

def move_stage_backgorund(app):
    #wait_until_ready()
    t1 = threading.Thread(target=move_stage, args=(app,))
    t1.start()
