import tkinter as tk

from data_manager import *

class BaseScreen(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.create_widgets()

        # Initialize AppData instead of using globals
        self.data = AppData()
        self.data.initialize_hardware()

    
    def create_widgets(self):
        # To be implemented by subclasses
        pass
        
    def on_show(self):
        # Called when screen becomes visible
        pass
        
    def on_hide(self):
        # Called when screen is hidden
        pass