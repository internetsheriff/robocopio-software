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
from tkinter import ttk, messagebox
from tkinter import Menu
from PIL import Image, ImageTk

import threading
from time import sleep

from stage_control import *
#from setup_manager import *
from data_manager import *
from base_screen import *



class AlignmentScreen(BaseScreen):
    def create_widgets(self):
        #self.config(bg='black')
        print("align screen shown")

        # Initialize AppData instead of using globals
        self.data = AppData()
        self.data.initialize_hardware()

        # Split screen: video feed on left, controls on right
        content_frame = ttk.Frame(self)
        content_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(content_frame, width=self.data.cap.get(cv2.CAP_PROP_FRAME_WIDTH)*0.5, 
                                height=self.data.cap.get(cv2.CAP_PROP_FRAME_HEIGHT)*0.5)
        self.canvas.pack(side=tk.LEFT, padx=10, pady=10)
        self.canvas.bind("<Double-Button-1>", self.on_double_click)

        # Controls panel
        controls_frame = ttk.Frame(content_frame, width=200)
        controls_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)
        controls_frame.pack_propagate(False)

        self.create_stage_controls(controls_frame)

        self.btn_snapshot = ttk.Button(controls_frame, text="Calculate shit", command=self.calculate_movment)
        self.btn_snapshot.pack(anchor=tk.CENTER, expand=True)

        self.btn_gay = ttk.Button(controls_frame, text="Plot shit", command=self.start_movement)
        self.btn_gay.pack(anchor=tk.CENTER, expand=True)

        # Add red cross toggle button
        self.red_cross_enabled = False
        self.btn_toggle_cross = ttk.Button(controls_frame, text="Enable Cross", command=self.toggle_red_cross)
        self.btn_toggle_cross.pack(anchor=tk.CENTER, expand=True)

        self.btn_set_origin = ttk.Button(controls_frame, text="Set Origin", command=self.set_origin)
        self.btn_set_origin.pack(anchor=tk.CENTER, expand=True)

        self.delay = 100  # Milliseconds
        self.update_frame()

    def create_stage_controls(self, parent):
        # Stage control title
        ttk.Label(parent, text="Stage Control", font=('Arial', 12, 'bold')).pack(pady=10)
        
        # Step size control
        step_frame = ttk.Frame(parent)
        step_frame.pack(pady=10)
        
        ttk.Label(step_frame, text="Step Size:").pack(side=tk.LEFT)
        self.step_size = tk.StringVar(value="100")
        step_entry = ttk.Entry(step_frame, textvariable=self.step_size, width=8)
        step_entry.pack(side=tk.LEFT, padx=5)
        ttk.Label(step_frame, text="μm").pack(side=tk.LEFT)
        
        # Arrow buttons frame
        arrows_frame = ttk.Frame(parent)
        arrows_frame.pack(pady=20)
        
        # Create arrow buttons (similar to your previous implementation)
        btn_size = 3
        
        # Up button
        self.btn_up = ttk.Button(arrows_frame, text="↑", width=btn_size,
                               command=lambda: self.move_stage_meters(0, int(self.step_size.get())/1000000, self.data))
        self.btn_up.grid(row=0, column=1, padx=5, pady=5)
        
        # Left, Stop, Right buttons
        self.btn_left = ttk.Button(arrows_frame, text="←", width=btn_size,
                                 command=lambda: self.move_stage_meters(-int(self.step_size.get())/1000000, 0, self.data))
        self.btn_left.grid(row=1, column=0, padx=5, pady=5)
        
        self.btn_stop = ttk.Button(arrows_frame, text="●", width=btn_size,
                                 command=lambda: self.controller.stage_controller.to_origin())
        self.btn_stop.grid(row=1, column=1, padx=5, pady=5)
        
        self.btn_right = ttk.Button(arrows_frame, text="→", width=btn_size,
                                  command=lambda: self.move_stage_meters( int(self.step_size.get())/1000000, 0, self.data))
        self.btn_right.grid(row=1, column=2, padx=5, pady=5)
        
        # Down button
        self.btn_down = ttk.Button(arrows_frame, text="↓", width=btn_size,
                                 command=lambda: self.move_stage_meters(0, -int(self.step_size.get())/1000000, self.data))
        self.btn_down.grid(row=2, column=1, padx=5, pady=5)

    def snapshot(self):
        # Get a frame from the video source
        if self.data.cap and self.data.cap.isOpened():
            ret, frame = self.data.cap.read()

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

        if self.data.cap and self.data.cap.isOpened():
            ret, frame = self.data.cap.read()

            if ret:
                if self.red_cross_enabled:
                    frame = self.draw_red_cross(frame)

                # Resize frame to fit canvas size
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()
                frame = cv2.resize(frame, (canvas_width, canvas_height))

                self.photo = ImageTk.PhotoImage(image=Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
                self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)

        self.after(self.delay, self.update_frame)

    def get_timestamp(self):
        import datetime
        return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


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

    def set_origin(self):
        confirm = messagebox.askyesno("Confirm Set Origin", "Are you sure you want to set the current position as the origin?")
        if confirm:
            self.controller.stage_controller.set_origin()
            messagebox.showinfo("Origin Set", "Origin has been successfully updated.")

    def on_double_click(self, event):
        x = event.x
        y = event.y
        dist_x_pixels = x - 640/2
        dist_y_pixels = -(y - 480/2)
        pixels_per_um = 0.475
        dist_x_meters = (dist_x_pixels/pixels_per_um)/1000000
        dist_y_meters = (dist_y_pixels/pixels_per_um)/1000000
        print(f"Double-click at relative position: ({x}, {y})")
        print(f"Dist: ({dist_x_meters}, {dist_y_meters})")
        self.controller.stage_controller.move_xy(dist_x_meters, dist_y_meters, self.data)

    def move_stage_meters(self, x_meters, y_meters, app_data):
        # Convert meters to steps using appdata configuration
        print(f'Received {y_meters} meters')
        #print(f'Meters per step =  {self.data.meters_per_step_y}')
        #print(f'Sending: {int(y_meters / self.data.meters_per_step_y)}')
        #x_steps = int(x_meters / self.data.meters_per_step_x)
        #y_steps = int(y_meters / self.data.meters_per_step_y)
        
        # Send steps to stage controller
        #self.controller.stage_controller.move_xy(x_steps, y_steps)

        self.controller.stage_controller.move_xy(x_meters, y_meters, app_data)
