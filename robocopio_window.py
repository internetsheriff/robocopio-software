import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import ttkbootstrap as tkb
from ttkbootstrap.constants import *

from configuration_screen import *
from alignment_screen import *
from run_screen import *

from stage_controller import *

class RobocopioWindow(tkb.Window):
    def __init__(self, window_title="Camera Application"):
        super().__init__(themename="darkly")
        self.title(window_title)

        #self.style = ttk.Style()
        #self.style.theme_use('clam')  # Windows modern theme

        self.stage_controller = StageController()
        self.stage_controller.connect()
        
        self.status_canvas = tk.Canvas(self, width=200, height=20, highlightthickness=0, bg=self['bg'])
        self.status_canvas.pack(side=tk.TOP, anchor=tk.W, padx=10, pady=5)

        self.status_led = self.status_canvas.create_oval(2, 2, 18, 18, fill="gray", outline="")

        self.status_text = self.status_canvas.create_text(30, 12, text="Status: Unknown", anchor="w", fill="white", font=("Segoe UI", 10))


        self.start_status_updater()

        # Store current screen
        self.current_screen = None
        
        # Create main container
        self.create_main_layout()
        
        # Create all screens (but don't show them yet)
        self.create_screens()
        
        # Show initial screen
        self.show_screen("configuration")
        
    def create_main_layout(self):
        # Main horizontal layout
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left navigation menu
        self.nav_frame = ttk.Frame(self.main_frame, width=200)
        self.nav_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.nav_frame.pack_propagate(False)  # Prevent shrinking
        
        # Right content area
        self.content_frame = ttk.Frame(self.main_frame)
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Create navigation buttons
        self.create_navigation()
    
    def create_navigation(self):
        # Navigation buttons - full height from top to bottom
        nav_buttons = [
            ("⚙️ Configuration", "configuration"),
            ("🎯 Alignment", "alignment"), 
            ("🚀 Run Experiment", "run")
        ]
        
        for text, screen_name in nav_buttons:
            print(screen_name)
            btn = ttk.Button(
                self.nav_frame, 
                text=text, 
                width=15,
                command=lambda sn=screen_name: self.show_screen(sn)
            )
            btn.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    def create_screens(self):
        # Dictionary to hold all screens
        self.screens = {}
        
        print("Creating screens...")
        
        try:
            print("Creating configuration screen...")
            self.screens["configuration"] = ConfigurationScreen(self.content_frame, self)
            print("Configuration screen created successfully")
        except Exception as e:
            print(f"Error creating configuration screen: {e}")
        
        try:
            print("Creating alignment screen...")
            self.screens["alignment"] = AlignmentScreen(self.content_frame, self)
            print("Alignment screen created successfully")
        except Exception as e:
            print(f"Error creating alignment screen: {e}")
        
        try:
            print("Creating run screen...")
            self.screens["run"] = RunScreen(self.content_frame, self)
            print("Run screen created successfully")
        except Exception as e:
            print(f"Error creating run screen: {e}")
        
        print(f"Final screens dictionary: {list(self.screens.keys())}")
        
        # Hide all screens initially
        for screen_name, screen in self.screens.items():
            if screen is not None:
                screen.pack_forget()
            else:
                print(f"Warning: Screen '{screen_name}' is None!")

    def show_screen(self, screen_name):
        print(f"Switching to screen: {screen_name}")
        
        # Hide current screen
        if self.current_screen:
            print(f"Hiding: {self.current_screen}")
            self.screens[self.current_screen].pack_forget()
        
        # Show new screen
        print(f"Showing: {screen_name}")
        self.screens[screen_name].pack(fill=tk.BOTH, expand=True)
        self.current_screen = screen_name
        
        # Optional: Call screen-specific setup
        self.screens[screen_name].on_show()
        
        print(f"Current screen is now: {self.current_screen}")

    def start_status_updater(self, interval_ms=1000):
        """Call this to begin periodic updates"""
        self.update_status()
        self.after(interval_ms, lambda: self.start_status_updater(interval_ms))

    def update_status(self):
        """Refresh the status label"""
        status = self.stage_controller.get_status()

        # Color and label updates
        color = {
            'READY': 'green',
            'ACK': 'orange',
            'ERROR': 'red',
            'DISCONNECTED': 'gray'
        }.get(status, 'gray')

        text = {
            'READY': 'READY',
            'ACK': 'BUSY',
            'ERROR': 'ERROR',
            'DISCONNECTED': 'DISCONNECTED'
        }.get(status, 'DISCONNECTED')

        self.status_canvas.itemconfig(self.status_led, fill=color)
        self.status_canvas.itemconfig(self.status_text, text=f"Status: {text}")