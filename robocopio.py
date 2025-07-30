import serial
import serial.tools.list_ports
import concurrent.futures
import time
from datetime import datetime
import os
import matplotlib.pyplot as plt
import cv2
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

import threading



pause_event = threading.Event()

cap = cv2.VideoCapture(1)
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

ser = serial.Serial('COM9', 115200, timeout=1)

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
        send_xy(movement[0]/meters_per_step_x,  movement[1]/meters_per_step_y);
        wait_until_ready()
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
    wait_until_ready()
    t1 = threading.Thread(target=move_stage, args=(app,))
    t1.start()


###### GLOBALS



picture_positions = []
border_positions = []
dish_centers = []
coordinat_list = []
movements_list = []

###### END GLOBALS
###### System setup
meters_per_step_x = 6.006e-06
meters_per_step_y = 3.508e-06

###### End system setup

###### Research parameters



#RESEARCHER = 'DP'
#PROJECT = 'BRT'
#LENS = '7X'
#LIGHT = 'B'



###### Box parameters

col_number = 4
row_number = 3

x_offset = 24.75e-03
y_offset = 16.68e-03
#x_offset = 2
#y_offset = 3

#x_offset = 21.75e-03
#y_offset = 14.82e-03

x_dish_step = 26.0e-03;
y_dish_step = 26.0e-03;

#x_dish_step = 1
#y_dish_step = 1
##### End Box parameters

##### Experiment parameters
BOX = 'C6'
experiment_folder = "C6_22"

dish_number = 7
dish_coordinates = [
    (0,0,"S10"),
    (1,0,"0V4"),
    (2,0,"0V5"),
    (3,0,"0V6"),
    (0,1,"004"),
    (1,1,"005"),
    (2,1,"006"),
    (3,1,"SIL"),
    (2,2,"0CP"),
    (3,2,"0CN"),
]
""" 
dish_coordinates = [
    (3,2,"0V7"),
    (2,2,"0V8"),
    (1,2,"0V9"),
    (0,2,"0V1"),
    (3,1,"A15"),
    (2,1,"0V2"),
    (1,1,"0V3"),
    (1,0,"0CP"),
    (0,0,"0CP"),
]   """

picture_matrix_side = 7
picture_step = 0.95e-03

border_matrix_side = 2
border_from_center = 6e-03

#picture_step = 0.1

##### End of Experiment parameters

class CameraApp(tk.Tk):
    def __init__(self, window, window_title="Camera Feed"):
        self.window = window
        self.window.title(window_title)

        self.vid = cap  # Open the default camera (0)

        self.canvas = tk.Canvas(window, width=self.vid.get(cv2.CAP_PROP_FRAME_WIDTH), 
                                height=self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.canvas.pack()

        self.btn_snapshot = tk.Button(window, text="Calculate shit", width=50, command=self.calculate_movment)
        self.btn_snapshot.pack(anchor=tk.CENTER, expand=True)

        self.btn_gay = tk.Button(window, text="Plot shit", width=50, command=self.start_movement)
        self.btn_gay.pack(anchor=tk.CENTER, expand=True)

        self.delay = 10  # Milliseconds
        self.update_frame()

        self.window.mainloop()

    def snapshot(self):
        # Get a frame from the video source
        ret, frame = self.vid.read()

        if ret:
            # Save the image
            cv2.imwrite("frame-" + str(self.get_timestamp()) + ".jpg", 
                        cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    def update_frame(self):
        # Get a frame from the video source
        ret, frame = self.vid.read()

        if ret:
            self.photo = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

        self.window.after(self.delay, self.update_frame)

    def get_timestamp(self):
        import datetime
        return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()

    def calculate_picture_positions(self):
        ##### Calculate Raster positions
        for y in range(picture_matrix_side):
            for x in range(picture_matrix_side):
                #picture_positions.append((-1*picture_step+x*picture_step, 1*picture_step-y*picture_step, y, x))
                px = -0.5 * (picture_matrix_side - 1) * picture_step + x * picture_step
                py = 0.5 * (picture_matrix_side - 1) * picture_step - y * picture_step
                picture_positions.append((px, py, y, x))  # (x, y, grid_row, grid_col)
        ##### End of Raster positions

        ##### Calculate Raster positions
        #for y in range(border_matrix_side):
        #    for x in range(border_matrix_side):
        #        border_positions.append((-0.5 * (border_matrix_side-1) * border_from_center + x * border_from_center, 0.5 * (border_matrix_side-1) * border_from_center - y * border_from_center, f'{y}{x}'))
        ##### End of Raster positions

        #for dx in [-border_matrix_side, border_matrix_side]:
        #    border_positions.append((dx, 0))  # (x, 0)
        #    print(f'Point added: {(dx, 0)}')

        #for dy in [-border_matrix_side, border_matrix_side]:
        #    border_positions.append((0, dy))  # (0, y)
        #    print(f'Point added: {(0, dy)}')

        for delta in [-border_from_center, border_from_center]:
            border_positions.append((delta, 0, 0 , 0))
            border_positions.append((0, delta, border_matrix_side, 0))

        for point in border_positions:
            print(point)

    def calculate_global_positions(self):
        ##### Calculate global positions
        coordinat_list.append((0,0, "origin", "PASS"))
        for dish in dish_coordinates:
            dish_centers.append((x_offset + dish[0]*x_dish_step, -y_offset - dish[1]*y_dish_step, dish[0], dish[1], dish[2]))

        for point in dish_centers:
            coordinat_list.append((point[0] , point[1], f'foc_sjust', "STOP"))
            for offset in picture_positions:
                if offset[2] == 0 and offset[3] == 0:
                    coordinat_list.append((point[0] + offset[0], point[1] + offset[1], f'{BOX}_{point[4]}_{point[2]}{point[3]}_00_{offset[2]:02d}_{offset[3]:02d}', "PASS"))
                else:
                    coordinat_list.append((point[0] + offset[0], point[1] + offset[1], f'{BOX}_{point[4]}_{point[2]}{point[3]}_00_{offset[2]:02d}_{offset[3]:02d}', "PASS"))
            
            for offset in border_positions:
                if offset[2] == 0 and offset[3] == 0:
                    coordinat_list.append((point[0] + offset[0], point[1] + offset[1], f'{BOX}_{point[4]}_{point[2]}{point[3]}_01_{offset[2]:02d}_{offset[3]:02d}', "STOP"))
                else:
                    coordinat_list.append((point[0] + offset[0], point[1] + offset[1], f'{BOX}_{point[4]}_{point[2]}{point[3]}_01_{offset[2]:02d}_{offset[3]:02d}', "PASS"))

        coordinat_list.append((0,0, "origin", "PASS"))


    def plot_picture_points(self):
        coodinates = [t[0:2] for t in coordinat_list]
        x_coordinates, y_coordinates = zip(*coodinates)

        fig, ax = plt.subplots()
        ax.scatter(x_coordinates, y_coordinates)
        ax.set_aspect('equal', adjustable='box')
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.title("Picture points")

        plt.show()

    def points_to_vectors(self):
        for i in range(1, len(coordinat_list)):
            prev_x, prev_y = coordinat_list[i-1][:2]
            curr_x, curr_y = coordinat_list[i][:2]
            dx = curr_x - prev_x  # Δx (change in X)
            dy = curr_y - prev_y  # Δy (change in Y)
            movements_list.append((dx, dy, coordinat_list[i][2], coordinat_list[i][3]))


    def plot_path(self):
        fig, ax = plt.subplots()
        last_point = (0,0)
        for point in movements_list:
            print(f'Last point: {last_point}')
            start_points_x = last_point[0]
            start_points_y = last_point[1]
            vector_components_u = point[0]
            vector_components_v = point[1]
            ax.quiver(start_points_x, start_points_y, vector_components_u, vector_components_v,
                    angles='xy', scale_units='xy', scale=1, color='blue')
            last_point = (last_point[0] + point[0], last_point[1] + point[1])
        ax.set_aspect('equal', adjustable='box')
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.title("Movements")
        plt.show()

    def calculate_movment(self):
        self.calculate_picture_positions()
        self.calculate_global_positions()
        self.points_to_vectors()
        self.plot_picture_points()
        self.plot_path()
        #experiment_folder = f'pictures_{datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}'
        #os.mkdir(experiment_folder)

    def start_movement(self):
        move_stage_backgorund(self)

    def ask_confirmation(self):
        response = messagebox.askyesno("Confirmation", "Continue movement?")
        if response:  # User clicked "Yes"
            pause_event.set()  # Resume the thread


# Create a Tkinter window and pass it to the CameraApp class
root = tk.Tk()
app = CameraApp(root)

