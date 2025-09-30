import threading
import serial
import time

class StageController:
    def __init__(self):
        self.ser = None
        self.is_connected = False
        self.running = False
        self.pause_event = threading.Event()
        self.pause_event.set()  # Start unpaused
        self.sequence_callback = None  # For UI notifications
    
    def connect(self):
        try:
            self.ser = serial.Serial('COM9', 115200, timeout=1)
            time.sleep(2)
            self.is_connected = True
            self.running = True
            return True
        except:
            return False
    
    def set_sequence_callback(self, callback):
        """Set callback for UI notifications"""
        self.sequence_callback = callback
    
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
            time.sleep(1)
            response = self.ser.readline().strip()
            if response == b'ACK':
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