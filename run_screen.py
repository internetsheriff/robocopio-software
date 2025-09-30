import cv2
import tkinter as tk

from base_screen import *

class RunScreen(BaseScreen):
    def create_widgets(self):
        self.config(bg='blue')
        print("run screen shown")

    def move_sequence_meters(self, movements_list_meters):
        # Convert entire sequence from meters to steps
        movements_list_steps = []
        for dx_meters, dy_meters, label, action in movements_list_meters:
            dx_steps = int(dx_meters / self.controller.data.meters_per_step_x)
            dy_steps = int(dy_meters / self.controller.data.meters_per_step_y)
            movements_list_steps.append((dx_steps, dy_steps, label, action))
        
        # Send steps to stage controller
        self.controller.stage_controller.move_sequence(movements_list_steps)

    def on_sequence_event(self, point_name, event_type):
        """Called by StageController for UI updates"""
        if event_type == "NEEDS_FOCUS":
            self.after(0, lambda: self.show_focus_alert(point_name))
        elif event_type == "SEQUENCE_COMPLETE":
            self.after(0, self.sequence_complete)
    
    def show_focus_alert(self, point_name):
        """Show manual focus requirement"""
        self.focus_label.config(text=f"Manual Focus Required at: {point_name}\nAdjust focus and click Continue")
        self.focus_alert_frame.pack(fill=tk.X, padx=20, pady=20)
        self.status_label.config(text=f"PAUSED: Manual focus required at {point_name}")
    
    def hide_focus_alert(self):
        """Hide focus controls"""
        self.focus_alert_frame.pack_forget()
    
    def resume_after_focus(self):
        """User confirms focus adjustment is complete"""
        self.controller.stage_controller.resume_sequence()
        self.hide_focus_alert()
        self.status_label.config(text="Resuming sequence...")
    
    def sequence_complete(self):
        """When entire sequence finishes"""
        self.status_label.config(text="Sequence Complete!")
        messagebox.showinfo("Complete", "Movement sequence finished successfully!")
    
    def start_sequence(self):
        """Start the movement sequence"""
        movements_list = self.controller.data.movements_list
        app_data = self.controller.data
        experiment_folder = self.controller.data.experiment_folder
        camera_capture = self.controller.data.cap  # Your camera object
        
        self.status_label.config(text="Sequence running...")
        success = self.controller.stage_controller.move_sequence(
            movements_list, app_data, experiment_folder, camera_capture
        )
        
        if not success:
            messagebox.showerror("Error", "Failed to start sequence")