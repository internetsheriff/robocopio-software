import serial
import serial.tools.list_ports
import concurrent.futures
import time
from datetime import datetime
import os

import yaml

import matplotlib.pyplot as plt
import cv2
import tkinter as tk
from tkinter import messagebox
from tkinter import Menu
from PIL import Image, ImageTk

import threading

from stage_control import *
#from setup_manager import *
from data_manager import *


class CameraApp(tk.Tk):
    def __init__(self, window, window_title="Camera Feed"):
        self.window = window
        self.window.title(window_title)

        self.create_menu()

        # Initialize AppData instead of using globals
        self.data = AppData()
        self.data.initialize_hardware()

        self.vid = self.data.cap  # Open the default camera (0)

        self.canvas = tk.Canvas(window, width=self.vid.get(cv2.CAP_PROP_FRAME_WIDTH), 
                                height=self.vid.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.canvas.pack()

        self.btn_snapshot = tk.Button(window, text="Calculate shit", width=50, command=self.calculate_movment)
        self.btn_snapshot.pack(anchor=tk.CENTER, expand=True)

        self.btn_gay = tk.Button(window, text="Plot shit", width=50, command=self.start_movement)
        self.btn_gay.pack(anchor=tk.CENTER, expand=True)

        # Add red cross toggle button
        self.red_cross_enabled = False
        self.btn_toggle_cross = tk.Button(window, text="Enable Cross", width=50, command=self.toggle_red_cross)
        self.btn_toggle_cross.pack(anchor=tk.CENTER, expand=True)

        self.delay = 10  # Milliseconds
        self.update_frame()

        self.window.mainloop()

    def create_menu(self):
        # Create menu bar
        menubar = Menu(self.window)
        self.window.config(menu=menubar)
        
        # File menu
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New", command=self.file_new)
        file_menu.add_command(label="Open", command=self.file_open)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.window.quit)
        
        # Camera menu
        camera_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Camera", menu=camera_menu)
        camera_menu.add_command(label="Take Snapshot", command=self.snapshot)
        camera_menu.add_command(label="Camera Settings", command=self.camera_settings)
        
        # Analysis menu
        analysis_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Analysis", menu=analysis_menu)
        analysis_menu.add_command(label="Calculate Movement", command=self.calculate_movment)
        analysis_menu.add_command(label="Plot Results", command=self.start_movement)
        analysis_menu.add_separator()
        analysis_menu.add_command(label="Clear Results", command=self.clear_results)
        
        # View menu
        view_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Fullscreen", command=self.toggle_fullscreen)
        view_menu.add_command(label="Zoom In", command=self.zoom_in)
        view_menu.add_command(label="Zoom Out", command=self.zoom_out)
        
        # Help menu
        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_command(label="Documentation", command=self.show_docs)

    # Menu command methods
    def file_new(self):
        print("New file created")
        # Add your new file logic here

    def file_open(self):
        print("Open file dialog")
        # Add file open logic here

    def camera_settings(self):
        print("Open camera settings")
        # Add camera settings dialog here

    def clear_results(self):
        print("Clear analysis results")
        # Add clear results logic here

    def toggle_fullscreen(self):
        print("Toggle fullscreen")
        # Add fullscreen toggle logic here

    def zoom_in(self):
        print("Zoom in")
        # Add zoom in logic here

    def zoom_out(self):
        print("Zoom out")
        # Add zoom out logic here

    def show_about(self):
        print("Show about dialog")
        # Add about dialog here

    def show_docs(self):
        print("Show documentation")
        # Add documentation display here


    def snapshot(self):
        # Get a frame from the video source
        ret, frame = self.vid.read()

        if ret:
            # Save the image
            cv2.imwrite("frame-" + str(self.get_timestamp()) + ".jpg", 
                        cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    def draw_red_cross(self, frame):
        # Get frame dimensions
        height, width = frame.shape[:2]
        
        # Calculate center coordinates
        center_x = width // 2
        center_y = height // 2
        
        # Define cross size
        cross_size = 30
        
        # Draw horizontal line (red color in BGR format)
        cv2.line(frame, 
                (center_x - cross_size, center_y), 
                (center_x + cross_size, center_y), 
                (0, 0, 255), 2)  # Red color, thickness 2
        
        # Draw vertical line (red color in BGR format)
        cv2.line(frame, 
                (center_x, center_y - cross_size), 
                (center_x, center_y + cross_size), 
                (0, 0, 255), 2)  # Red color, thickness 2
        
        return frame

    def update_frame(self):
        # Get a frame from the video source
        ret, frame = self.vid.read()

        if ret:
            if self.red_cross_enabled:
                frame = self.draw_red_cross(frame)

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
        for y in range(self.data.picture_matrix_side):
            for x in range(self.data.picture_matrix_side):
                #self.data.picture_positions.append((-1*self.data.picture_step+x*self.data.picture_step, 1*self.data.picture_step-y*self.data.picture_step, y, x))
                px = -0.5 * (self.data.picture_matrix_side - 1) * self.data.picture_step + x * self.data.picture_step
                py = 0.5 * (self.data.picture_matrix_side - 1) * self.data.picture_step - y * self.data.picture_step
                self.data.picture_positions.append((px, py, y, x))  # (x, y, grid_row, grid_col)
        ##### End of Raster positions

        ##### Calculate Raster positions
        #for y in range(self.data.border_matrix_side):
        #    for x in range(self.data.border_matrix_side):
        #        self.data.border_positions.append((-0.5 * (self.data.border_matrix_side-1) * self.data.border_from_center + x * self.data.border_from_center, 0.5 * (self.data.border_matrix_side-1) * self.data.border_from_center - y * self.data.border_from_center, f'{y}{x}'))
        ##### End of Raster positions

        #for dx in [-self.data.border_matrix_side, self.data.border_matrix_side]:
        #    self.data.border_positions.append((dx, 0))  # (x, 0)
        #    print(f'Point added: {(dx, 0)}')

        #for dy in [-self.data.border_matrix_side, self.data.border_matrix_side]:
        #    self.data.border_positions.append((0, dy))  # (0, y)
        #    print(f'Point added: {(0, dy)}')

        for delta in [-self.data.border_from_center, self.data.border_from_center]:
            self.data.border_positions.append((delta, 0, 0 , 0))
            self.data.border_positions.append((0, delta, self.data.border_matrix_side, 0))

        for point in self.data.border_positions:
            print(point)

    def calculate_global_positions(self):
        ##### Calculate global positions
        self.data.coordinat_list.append((0,0, "origin", "PASS"))
        for dish in self.data.dish_coordinates:
            self.data.dish_centers.append((self.data.x_offset + dish[0]*self.data.x_dish_step, -self.data.y_offset - dish[1]*self.data.y_dish_step, dish[0], dish[1], dish[2]))

        for point in self.data.dish_centers:
            self.data.coordinat_list.append((point[0] , point[1], f'foc_sjust', "STOP"))
            for offset in self.data.picture_positions:
                if offset[2] == 0 and offset[3] == 0:
                    self.data.coordinat_list.append((point[0] + offset[0], point[1] + offset[1], f'{self.data.box_name}_{point[4]}_{point[2]}{point[3]}_00_{offset[2]:02d}_{offset[3]:02d}', "PASS"))
                else:
                    self.data.coordinat_list.append((point[0] + offset[0], point[1] + offset[1], f'{self.data.box_name}_{point[4]}_{point[2]}{point[3]}_00_{offset[2]:02d}_{offset[3]:02d}', "PASS"))
            
            for offset in self.data.border_positions:
                if offset[2] == 0 and offset[3] == 0:
                    self.data.coordinat_list.append((point[0] + offset[0], point[1] + offset[1], f'{self.data.box_name}_{point[4]}_{point[2]}{point[3]}_01_{offset[2]:02d}_{offset[3]:02d}', "STOP"))
                else:
                    self.data.coordinat_list.append((point[0] + offset[0], point[1] + offset[1], f'{self.data.box_name}_{point[4]}_{point[2]}{point[3]}_01_{offset[2]:02d}_{offset[3]:02d}', "PASS"))

        self.data.coordinat_list.append((0,0, "origin", "PASS"))


    def plot_picture_points(self):
        coodinates = [t[0:2] for t in self.data.coordinat_list]
        x_coordinates, y_coordinates = zip(*coodinates)

        fig, ax = plt.subplots()
        ax.scatter(x_coordinates, y_coordinates)
        ax.set_aspect('equal', adjustable='box')
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.title("Picture points")

        plt.show()

    def points_to_vectors(self):
        for i in range(1, len(self.data.coordinat_list)):
            prev_x, prev_y = self.data.coordinat_list[i-1][:2]
            curr_x, curr_y = self.data.coordinat_list[i][:2]
            dx = curr_x - prev_x  # Δx (change in X)
            dy = curr_y - prev_y  # Δy (change in Y)
            self.data.movements_list.append((dx, dy, self.data.coordinat_list[i][2], self.data.coordinat_list[i][3]))


    def plot_path(self):
        fig, ax = plt.subplots()
        last_point = (0,0)
        for point in self.data.movements_list:
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

    def toggle_red_cross(self):
        self.red_cross_enabled = not self.red_cross_enabled
        if self.red_cross_enabled:
            self.btn_toggle_cross.config(text="Disable Red Cross")
        else:
            self.btn_toggle_cross.config(text="Enable Red Cross")

# Create a Tkinter window and pass it to the CameraApp class
root = tk.Tk()
app = CameraApp(root)
