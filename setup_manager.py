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


################ SYSTEM SETUP ###################

with open("system_setup.yaml") as f:
    system_setup = yaml.load(f, Loader=yaml.FullLoader)

equipment_name = system_setup['equipment_name']
meters_per_step_x = system_setup['meters_per_step_x']
meters_per_step_y = system_setup['meters_per_step_y']

############ END OF SYSTEM SETUP ################

############ RESEARCH PARAMETERS ################

#RESEARCHER = 'DP'
#PROJECT = 'BRT'
#LENS = '7X'
#LIGHT = 'B'

######### END OF RESEARCH PARAMETERS ############

################ BOX PARAMETERS #################

with open("box_setup.yaml") as f:
    box_setup = yaml.load(f, Loader=yaml.FullLoader)

box_type = box_setup['box_type']
col_number = box_setup['col_number']
row_number = box_setup['row_number']

x_offset = box_setup['x_offset']
y_offset = box_setup['y_offset']

x_dish_step = box_setup['x_dish_step']
y_dish_step = box_setup['y_dish_step']

############# END OF BOX PARAMETERS #############

############# EXPERIMENT PARAMETERS #############

with open("experiment_setup.yaml") as f:
    experiment_setup = yaml.load(f, Loader=yaml.FullLoader)

dish_coordinates_changed = [tuple(item) for item in experiment_setup['dish_coordinates']]

BOX = experiment_setup['box_name']
experiment_folder = experiment_setup['experiment_folder']

picture_matrix_side = experiment_setup['picture_matrix_side']
picture_step = experiment_setup['picture_step']

border_matrix_side = experiment_setup['border_matrix_side']
border_from_center = experiment_setup['border_from_center']

dish_number = experiment_setup['dish_number']

dish_coordinates = [tuple(item) for item in experiment_setup['dish_coordinates']]


######## END OF EXPERIMENT PARAMETERS ###########


########## INITIALIZE CORE VARIABLES ############
pause_event = threading.Event()

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("Error: Could not open camera.")
    exit()

#ser = serial.Serial('COM9', 115200, timeout=1)

###### END OF INITIALIZE CORE VARIABLES ########

############ CREATE GLOBALS ####################

picture_positions = []
border_positions = []
dish_centers = []
coordinat_list = []
movements_list = []

########## END OF CREATE GLOBALS ##############

