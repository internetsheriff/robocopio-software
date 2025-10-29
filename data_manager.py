import threading
import cv2
import yaml

class AppData:
    def __init__(self):
        # System Setup
        self.equipment_name = ""
        self.meters_per_step_x = 0
        self.meters_per_step_y = 0
        
        # Box Parameters
        self.box_type = ""
        self.col_number = 0
        self.row_number = 0
        self.x_offset = 0
        self.y_offset = 0
        self.x_dish_step = 0
        self.y_dish_step = 0
        
        # Experiment Parameters
        self.box_name = ""
        self.experiment_folder = ""
        self.picture_matrix_side = 0
        self.picture_step = 0
        self.border_matrix_side = 0
        self.border_from_center = 0
        self.dish_number = 0
        self.dish_coordinates = []
        
        # Core Variables
        self.pause_event = threading.Event()
        self._cap = None
        self._ser = None
        self.mode = "Backlash correction off"
        
        # Runtime Data
        self.picture_positions = []
        self.border_positions = []
        self.dish_centers = []
        self.coordinat_list = []
        self.movements_list = []
        
        # Load initial data from YAML files
        self.load_system_setup()
        self.load_box_setup()
        self.load_experiment_setup()

    @property
    def cap(self):
        return self._cap
    
    @property
    def ser(self):
        return self._ser

    def load_system_setup(self):
        """Load data from YAML configuration files"""
        try:
            # Load system setup
            with open("system_setup.yaml") as f:
                system_setup = yaml.load(f, Loader=yaml.FullLoader)
                self.equipment_name = system_setup['equipment_name']
                self.meters_per_step_x = system_setup['meters_per_step_x']
                self.meters_per_step_y = system_setup['meters_per_step_y']
             
        except FileNotFoundError as e:
            print(f"Configuration file not found: {e}")
        except KeyError as e:
            print(f"Missing key in configuration file: {e}")
        except Exception as e:
            print(f"Error loading configuration: {e}")

    def load_box_setup(self):
        """Load data from YAML configuration files"""
        try:
            # Load box setup
            with open("box_setup.yaml") as f:
                box_setup = yaml.load(f, Loader=yaml.FullLoader)
                self.box_type = box_setup['box_type']
                self.col_number = box_setup['col_number']
                self.row_number = box_setup['row_number']
                self.x_offset = box_setup['x_offset']
                self.y_offset = box_setup['y_offset']
                self.x_dish_step = box_setup['x_dish_step']
                self.y_dish_step = box_setup['y_dish_step']
             
        except FileNotFoundError as e:
            print(f"Configuration file not found: {e}")
        except KeyError as e:
            print(f"Missing key in configuration file: {e}")
        except Exception as e:
            print(f"Error loading configuration: {e}")

    def load_experiment_setup(self):
        """Load data from YAML configuration files"""
        try:
            # Load experiment setup
            with open("experiment_setup.yaml") as f:
                experiment_setup = yaml.load(f, Loader=yaml.FullLoader)
                self.box_name = experiment_setup['box_name']
                self.experiment_folder = experiment_setup['experiment_folder']
                self.picture_matrix_side = experiment_setup['picture_matrix_side']
                self.picture_step = experiment_setup['picture_step']
                self.border_matrix_side = experiment_setup['border_matrix_side']
                self.border_from_center = float(experiment_setup['border_from_center'])
                self.dish_number = experiment_setup['dish_number']
                self.dish_coordinates = [tuple(item) for item in experiment_setup['dish_coordinates']]
                
        except FileNotFoundError as e:
            print(f"Configuration file not found: {e}")
        except KeyError as e:
            print(f"Missing key in configuration file: {e}")
        except Exception as e:
            print(f"Error loading configuration: {e}")

    def initialize_hardware(self):
        """Initialize camera and serial connection"""
        try:
            # Initialize camera
            self._cap = cv2.VideoCapture(0)
            if not self._cap.isOpened():
                raise Exception("Could not open camera")
            
            # Test camera by grabbing one frame
            ret, frame = self._cap.read()
            if not ret:
                print("ERROOOOOOOOOOOOO")
                self.release_camera()
                #raise Exception("Could not read frame from camera")
                self._cap = cv2.VideoCapture(0)
                if not self._cap.isOpened():
                    raise Exception("Could not open cameraaaaaaaaaaa")
                
                # Test camera by grabbing one frame
                ret, frame = self._cap.read()
                if not ret:
                    self.release_camera()
                    raise Exception("Could not read frame from cameraaaaaaaaaaaaaaaaaaaa")
            
            # Initialize serial
            #self._ser = serial.Serial('COM9', 115200, timeout=1)
            print("Hardware initialized successfully")
            
        except Exception as e:
            print(f"Hardware initialization error: {e}")
            self.cleanup()
            raise

    def save_system_setup(self):
        """Save system setup back to YAML"""
        system_setup = {
            'equipment_name': self.equipment_name,
            'meters_per_step_x': self.meters_per_step_x,
            'meters_per_step_y': self.meters_per_step_y
        }
        with open("system_setup.yaml", 'w') as f:
            yaml.dump(system_setup, f)
    
    def save_box_setup(self):
        """Save box setup back to YAML"""
        box_setup = {
            'box_type': self.box_type,
            'col_number': self.col_number,
            'row_number': self.row_number,
            'x_offset': self.x_offset,
            'y_offset': self.y_offset,
            'x_dish_step': self.x_dish_step,
            'y_dish_step': self.y_dish_step
        }
        with open("box_setup.yaml", 'w') as f:
            yaml.dump(box_setup, f)
    
    def save_experiment_setup(self):
        """Save experiment setup back to YAML"""
        experiment_setup = {
            'box_name': self.box_name,
            'experiment_folder': self.experiment_folder,
            'picture_matrix_side': self.picture_matrix_side,
            'picture_step': self.picture_step,
            'border_matrix_side': self.border_matrix_side,
            'border_from_center': self.border_from_center,
            'dish_number': self.dish_number,
            'dish_coordinates': self.dish_coordinates
        }
        with open("experiment_setup.yaml", 'w') as f:
            yaml.dump(experiment_setup, f)

    def clear_runtime_data(self):
        """Clear all runtime-generated data"""
        self.picture_positions.clear()
        self.border_positions.clear()
        self.dish_centers.clear()
        self.coordinat_list.clear()
        self.movements_list.clear()
    
    def release_camera(self):
        """Safely release camera resources"""
        if self._cap and self._cap.isOpened():
            self._cap.release()
            self._cap = None
            print("Camera released")
    
    def release_serial(self):
        """Safely release serial resources"""
        if self._ser and self._ser.is_open:
            self._ser.close()
            self._ser = None
            print("Serial port released")
    
    def cleanup(self):
        """Release all hardware resources"""
        self.release_camera()
        self.release_serial()
    
    def __del__(self):
        """Destructor to ensure resources are released"""
        self.cleanup()