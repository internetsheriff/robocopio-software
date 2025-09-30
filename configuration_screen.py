import cv2
import tkinter as tk

from base_screen import *

class ConfigurationScreen(BaseScreen):
    def create_widgets(self):
        self.config(bg='green')
        print("config screen shown")