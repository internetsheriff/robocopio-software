import threading
import serial
import time
import yaml
import cv2

import numpy as np

class StageController:
    def __init__(self):
        self.ser = None
        self.is_connected = False
        self.running = False
        self.pause_event = threading.Event()
        self.pause_event.set()  # Start unpaused
        self.sequence_callback = None  # For UI notifications

        with open('position.yaml', 'r') as file:
            position = yaml.safe_load(file)
            x = position.get('x', 0)
            y = position.get('y', 0)

        self.origin = [x,y]
        
    def connect(self):
        ports = serial.tools.list_ports.comports()
        for port in ports:
            print(port)
        for port in ports:
            try:
                print(f"Trying port: {port.device}")
                ser = serial.Serial(port.device, 115200, timeout=1)
                time.sleep(1)  # Give the device time to initialize

                ser.write(b'STATUS?\n')
                response = ser.readline().strip()

                if response == b'READY':
                    print(f"Connected to device at {port.device}")
                    self.ser = ser
                    self.is_connected = True
                    self.running = True
                    return True
                else:
                    ser.close()  # Not our device, close the port
            except Exception as e:
                print(f"Error with port {port.device}: {e}")
                continue  # Try next port

        print("Device not found.")
        return False
    
    def set_sequence_callback(self, callback):
        """Set callback for UI notifications"""
        self.sequence_callback = callback

    def move_xy(self, x_meters, y_meters, app_data, max_retries = 3):
        #self._send_xy(x, y)
        #    wait_until_ready()
        print(f'Received x: {x_meters}, y: {y_meters} meters')
        print(f'Meters per step x: {app_data.meters_per_step_x}')
        print(f'Meters per step y: {app_data.meters_per_step_y}')

        x_steps = int(x_meters / app_data.meters_per_step_x)
        y_steps = int(y_meters / app_data.meters_per_step_y)

        print(f'Sending x: {x_steps}, y: {y_steps}')

        t1 = threading.Thread(target=self._send_xy_backlash, args=(x_steps, y_steps, app_data.cap))
        #t1 = threading.Thread(target=self._send_xy, args=(x_steps, y_steps))
        t1.start()

    
    def move_sequence(self, movements_list, app_data, experiment_folder, camera_capture):
        """Execute movement sequence with pauses and image capture"""
        if not self.is_connected:
            return False
        
        thread = threading.Thread(
            target=self._move_sequence_thread,
            args=(movements_list, app_data, experiment_folder, camera_capture)
        )
        thread.daemon = True
        thread.start()
        return True
    
    def _move_sequence_thread(self, movements_list, app_data, experiment_folder, camera_capture):
        """Background thread that replicates your exact workflow"""
        for idx, movement in enumerate(movements_list):
            # Convert meters to steps
            dx_steps = int(movement[0] / app_data.meters_per_step_x)
            dy_steps = int(movement[1] / app_data.meters_per_step_y)
            
            # Move stage
            self._send_xy(dx_steps, dy_steps)
            self._wait_until_ready()
            
            # Check if STOP point for manual focus
            if movement[3] == "STOP":
                self.pause_event.clear()
                # Notify UI that manual focus is needed
                if self.sequence_callback:
                    self.sequence_callback(movement[2], "NEEDS_FOCUS")
                # Wait for user confirmation
                self.pause_event.wait()
            
            # Capture image after every movement
            ret, frame = camera_capture.read()
            if ret:
                cv2.imwrite(f'{experiment_folder}/{movement[2]}.png', frame)
                print(f'Image saved: {experiment_folder}/{movement[2]}.png')
            
            print(f'Completed movement {idx+1}/{len(movements_list)}: {movement[2]}')
        
        # Notify completion
        if self.sequence_callback:
            self.sequence_callback("", "SEQUENCE_COMPLETE")
        print('DONE')
    
    def resume_sequence(self):
        """Resume after manual focus adjustment"""
        self.pause_event.set()
    
    def _send_xy(self, x_steps, y_steps, max_retries=3):
        """Your existing send_xy function"""
        msg = f"\x02{x_steps},{y_steps}\x03".encode()
        for attempt in range(max_retries):
            self.ser.write(msg)
            time.sleep(0.5)
            response = self.ser.readline().strip()
            if response == b'ACK':
                self.update_origin(x_steps, y_steps)
                return True
        return False

    def frames_different(self, frame1, frame2):
        threshold_max=5
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        diff = cv2.absdiff(gray1, gray2)
        mean_diff = np.mean(diff)
        print(f"[Compare] Mean pixel difference: {mean_diff:.2f}")
        return mean_diff > threshold_max
    
    def _send_xy_backlash(self, x_steps, y_steps, camera_capture=None, max_retries=3):
        """Your existing send_xy function"""
        max_movements = 40
        test_step = 1
        movement_threshold = 5

        x_test_step = test_step * np.sign(x_steps)
        y_test_step = test_step * np.sign(y_steps)

        print("[Backlash Check] Verifying real movement...")
        if camera_capture is None:
            print("[Backlash Check] Failed to capture initial frame: camarea is None")
            return False

        #check of x
        if x_steps != 0:
            # Capture initial x frame
            ret1, frame_before = camera_capture.read()
            if not ret1:
                print("[Backlash Check] Failed to capture initial x frame: cant read")
                return False

            for attempt in range(max_movements):
                msg = f"\x02{x_test_step},{0}\x03".encode()
                
                self.ser.write(msg)
                time.sleep(0.3)
                response = self.ser.readline().strip()
                if response == b'NACK':
                    print(F"[Backlash Check] X: Failed to move stage. Response: {response}")
                    continue  # Try again

                print("[Backlash Check] X:  Movement started")
                # Wait until stage is ready
                self._wait_until_ready()
                            
                print("[Backlash Check] X:Movent done")
                # Capture new frame
                ret2, frame_after = camera_capture.read()
                if not ret2:
                    print("[Backlash Check] Failed to capture frame after move: cant read")
                    return False      

                if self.frames_different(frame_before, frame_after):
                    print("[Backlash Check] Movement detected in X after", attempt + 1, "attempt(s)")
                    break  # Stage has moved  
                
                print(f"[Backlash Check] No movement detected in X after {attempt +1} attemps")

        else:
            print("[Backlash Check] No movent in x, skipping anti backlash") 

        if y_steps != 0:
            for attempt in range(max_movements):
                # Capture initial x frame
                ret1, frame_before = camera_capture.read()
                if not ret1:
                    print("[Backlash Check] Failed to capture initial y frame: cant read")
                    return False

                msg = f"\x02{0},{y_test_step}\x03".encode()
                
                self.ser.write(msg)
                time.sleep(0.3)
                response = self.ser.readline().strip()
                if response == b'NACK':
                    print(F"[Backlash Check] Y: Failed to move stage. Response: {response}")
                    continue  # Try again

                print("[Backlash Check] Y: Movment started")
                # Wait until stage is ready
                self._wait_until_ready()
                            
                print("[Backlash Check] Y: Movement stopped")
                # Capture new frame
                ret2, frame_after = camera_capture.read()
                if not ret2:
                    print("[Backlash Check] Y: Failed to capture frame after move: cant read")
                    return False      

                if self.frames_different(frame_before, frame_after):
                    print("[Backlash Check] Movement detected in Y after", attempt + 1, "attempt(s)")
                    break  # Stage has moved  
                
                print(f"[Backlash Check] No movement detected in Y after {attempt +1} attemps") 
        else:
            print("[Backlash Check] No movent in y, skipping anti backlash") 

        time.sleep(1)
        msg = f"\x02{x_steps},{y_steps}\x03".encode()
        for attempt in range(max_retries):
            self.ser.write(msg)
            time.sleep(1)
            response = self.ser.readline().strip()
            print(F"[Backlash MOVEMENT] AFTER RESPONSE: {response}")
            if response == b'ACK':
                self.update_origin(x_steps, y_steps)
                return True
        return False

    def _wait_until_ready(self):
        """Your existing wait_until_ready function"""
        while True:
            self.ser.write(b'STATUS?\n')
            status = self.ser.readline().strip()
            if status == b'READY':
                return
            time.sleep(0.2)

    def update_origin(self, x, y):
        self.origin[0] += x
        self.origin[1] += y
        data = {'x': self.origin[0], 'y': self.origin[1]}
        with open('position.yaml', 'w') as file:
            yaml.dump(data, file)

    def set_origin(self):
        self.origin[0] = 0
        self.origin[1] = 0
        data = {'x': self.origin[0], 'y': self.origin[1]}
        with open('position.yaml', 'w') as file:
            yaml.dump(data, file)
        print('NEW ORIGIN SET')

    def to_origin(self):
        x = - self.origin[0]
        y = - self.origin[1]
        print(f'Back to origin -> x: {x}, y: {y}')

    def get_status(self):
        return 'DISCONNECTED'
"""         if self.ser and self.ser.is_open:
            try:
                self.ser.write(b'STATUS?\n')
                status = self.ser.readline().strip()
                return status.decode()  
            except Exception as e:
                return 'ERROR'
        return 'DISCONNECTED' """
        