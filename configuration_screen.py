import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import yaml
import os
from base_screen import *

class ConfigurationScreen(BaseScreen):
    def create_widgets(self):
        # Main container
        self.config(bg='white')
        
        # Title
        title_label = ttk.Label(self, text="Configuration", font=('Arial', 16, 'bold'), background='white')
        title_label.pack(pady=10)
        
        # Project selection frame
        project_frame = ttk.Frame(self, style='Card.TFrame')
        project_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.project_path = tk.StringVar()
        ttk.Label(project_frame, text="Project:", background='white', font=('Arial', 10)).pack(side=tk.LEFT)
        ttk.Entry(project_frame, textvariable=self.project_path, width=50, state='readonly').pack(side=tk.LEFT, padx=5)
        ttk.Button(project_frame, text="Open Project", command=self.open_project).pack(side=tk.LEFT, padx=5)
        ttk.Button(project_frame, text="New Project", command=self.new_project).pack(side=tk.LEFT, padx=5)
        
        # Notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Create tabs
        self.experiment_frame = ttk.Frame(self.notebook)
        self.sample_frame = ttk.Frame(self.notebook)
        self.system_frame = ttk.Frame(self.notebook)
        self.upstream_frame = ttk.Frame(self.notebook)
        
        self.notebook.add(self.experiment_frame, text="Experiment")
        self.notebook.add(self.sample_frame, text="Sample")
        self.notebook.add(self.system_frame, text="System")
        self.notebook.add(self.upstream_frame, text="Upstream")
        
        # Initialize tab contents
        self.create_experiment_tab()
        self.create_sample_tab()
        self.create_system_tab()
        self.create_upstream_tab()
        
        # Load initial data
        self.load_config_data()
    
    def create_experiment_tab(self):
        # Experiment configuration
        main_frame = ttk.Frame(self.experiment_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create scrollable frame
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        self.experiment_scrollable_frame = ttk.Frame(canvas)
        
        self.experiment_scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.experiment_scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Experiment fields
        self.experiment_vars = {}
        fields = [
            ('box_name', 'Box Name:', 'str'),
            ('experiment_folder', 'Experiment Folder:', 'str'),
            ('picture_matrix_side', 'Picture Matrix Side:', 'int'),
            ('picture_step', 'Picture Step (mm):', 'float'),
            ('border_matrix_side', 'Border Matrix Side:', 'int'),
            ('border_from_center', 'Border From Center (mm):', 'float'),
            ('dish_number', 'Dish Number:', 'int'),
        ]
        
        for i, (key, label, dtype) in enumerate(fields):
            ttk.Label(self.experiment_scrollable_frame, text=label).grid(row=i, column=0, sticky='w', pady=5)
            if dtype == 'str':
                var = tk.StringVar()
                entry = ttk.Entry(self.experiment_scrollable_frame, textvariable=var, width=30)
            elif dtype == 'int':
                var = tk.IntVar()
                entry = ttk.Entry(self.experiment_scrollable_frame, textvariable=var, width=30)
            elif dtype == 'float':
                var = tk.DoubleVar()
                entry = ttk.Entry(self.experiment_scrollable_frame, textvariable=var, width=30)
            
            entry.grid(row=i, column=1, sticky='w', pady=5, padx=10)
            self.experiment_vars[key] = var
        
        # Dish coordinates (simplified - you might want a more complex widget for this)
        ttk.Label(self.experiment_scrollable_frame, text="Dish Coordinates:").grid(row=len(fields), column=0, sticky='w', pady=5)
        self.dish_coordinates_text = tk.Text(self.experiment_scrollable_frame, width=30, height=5)
        self.dish_coordinates_text.grid(row=len(fields), column=1, sticky='w', pady=5, padx=10)
        
        # Save button
        ttk.Button(self.experiment_scrollable_frame, text="Save Experiment Config", 
                  command=self.save_experiment_config).grid(row=len(fields)+1, column=0, columnspan=2, pady=20)
    
    def create_sample_tab(self):
        main_frame = ttk.Frame(self.sample_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.sample_vars = {}
        fields = [
            ('box_type', 'Box Type:', 'str'),
            ('col_number', 'Number of Columns:', 'int'),
            ('row_number', 'Number of Rows:', 'int'),
            ('x_offset', 'X Offset (mm):', 'float'),
            ('y_offset', 'Y Offset (mm):', 'float'),
            ('x_dish_step', 'X Dish Step (mm):', 'float'),
            ('y_dish_step', 'Y Dish Step (mm):', 'float'),
        ]
        
        for i, (key, label, dtype) in enumerate(fields):
            ttk.Label(main_frame, text=label).grid(row=i, column=0, sticky='w', pady=5)
            if dtype == 'str':
                var = tk.StringVar()
                entry = ttk.Entry(main_frame, textvariable=var, width=30)
            elif dtype == 'int':
                var = tk.IntVar()
                entry = ttk.Entry(main_frame, textvariable=var, width=30)
            elif dtype == 'float':
                var = tk.DoubleVar()
                entry = ttk.Entry(main_frame, textvariable=var, width=30)
            
            entry.grid(row=i, column=1, sticky='w', pady=5, padx=10)
            self.sample_vars[key] = var
        
        ttk.Button(main_frame, text="Save Sample Config", 
                  command=self.save_sample_config).grid(row=len(fields), column=0, columnspan=2, pady=20)
    
    def create_system_tab(self):
        main_frame = ttk.Frame(self.system_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.system_vars = {}
        fields = [
            ('equipment_name', 'Equipment Name:', 'str'),
            ('meters_per_step_x', 'Meters per Step X:', 'float'),
            ('meters_per_step_y', 'Meters per Step Y:', 'float'),
        ]
        
        for i, (key, label, dtype) in enumerate(fields):
            ttk.Label(main_frame, text=label).grid(row=i, column=0, sticky='w', pady=5)
            if dtype == 'str':
                var = tk.StringVar()
                entry = ttk.Entry(main_frame, textvariable=var, width=30)
            elif dtype == 'float':
                var = tk.DoubleVar()
                entry = ttk.Entry(main_frame, textvariable=var, width=30)
            
            entry.grid(row=i, column=1, sticky='w', pady=5, padx=10)
            self.system_vars[key] = var
        
        ttk.Button(main_frame, text="Save System Config", 
                  command=self.save_system_config).grid(row=len(fields), column=0, columnspan=2, pady=20)
    
    def create_upstream_tab(self):
        main_frame = ttk.Frame(self.upstream_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Placeholder for upstream configuration
        ttk.Label(main_frame, text="Upstream Configuration", font=('Arial', 12, 'bold')).pack(pady=20)
        ttk.Label(main_frame, text="Configure data export, API connections, etc.").pack(pady=10)
        
        # Add your upstream-specific fields here
        self.upstream_vars = {}
        # Example fields:
        # fields = [('api_url', 'API URL:', 'str'), ...]
        
        ttk.Button(main_frame, text="Save Upstream Config").pack(pady=20)
    
    def open_project(self):
        """Open existing project directory"""
        project_dir = filedialog.askdirectory(title="Select Project Directory")
        if project_dir:
            self.project_path.set(project_dir)
            self.load_config_data()
    
    def new_project(self):
        """Create new project directory"""
        project_dir = filedialog.askdirectory(title="Select Directory for New Project")
        if project_dir:
            project_name = filedialog.asksaveasfilename(
                title="Name your project",
                defaultextension="",
                initialdir=project_dir
            )
            if project_name:
                self.project_path.set(os.path.join(project_dir, project_name))
                os.makedirs(self.project_path.get(), exist_ok=True)
                # Create default config files
                self.create_default_configs()
                self.load_config_data()
    
    def load_config_data(self):
        """Load configuration data from YAML files"""
        project_dir = self.project_path.get() if self.project_path.get() else "."
        
        try:
            # Load experiment config
            exp_path = os.path.join(project_dir, "experiment_setup.yaml")
            if os.path.exists(exp_path):
                with open(exp_path, 'r') as f:
                    exp_data = yaml.safe_load(f)
                    for key, var in self.experiment_vars.items():
                        if key in exp_data:
                            var.set(exp_data[key])
                    if 'dish_coordinates' in exp_data:
                        self.dish_coordinates_text.delete(1.0, tk.END)
                        self.dish_coordinates_text.insert(1.0, str(exp_data['dish_coordinates']))
            
            # Load sample config
            sample_path = os.path.join(project_dir, "box_setup.yaml")
            if os.path.exists(sample_path):
                with open(sample_path, 'r') as f:
                    sample_data = yaml.safe_load(f)
                    for key, var in self.sample_vars.items():
                        if key in sample_data:
                            var.set(sample_data[key])
            
            # Load system config
            system_path = os.path.join(project_dir, "system_setup.yaml")
            if os.path.exists(system_path):
                with open(system_path, 'r') as f:
                    system_data = yaml.safe_load(f)
                    for key, var in self.system_vars.items():
                        if key in system_data:
                            var.set(system_data[key])
                            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load configuration: {e}")
    
    def save_experiment_config(self):
        """Save experiment configuration to YAML"""
        try:
            data = {key: var.get() for key, var in self.experiment_vars.items()}
            # Parse dish coordinates from text
            dish_text = self.dish_coordinates_text.get(1.0, tk.END).strip()
            if dish_text:
                data['dish_coordinates'] = eval(dish_text)  # Be careful with eval!
            
            project_dir = self.project_path.get() if self.project_path.get() else "."
            with open(os.path.join(project_dir, "experiment_setup.yaml"), 'w') as f:
                yaml.dump(data, f, default_flow_style=False)
            
            messagebox.showinfo("Success", "Experiment configuration saved!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save experiment config: {e}")
    
    def save_sample_config(self):
        """Save sample configuration to YAML"""
        try:
            data = {key: var.get() for key, var in self.sample_vars.items()}
            
            project_dir = self.project_path.get() if self.project_path.get() else "."
            with open(os.path.join(project_dir, "box_setup.yaml"), 'w') as f:
                yaml.dump(data, f, default_flow_style=False)
            
            messagebox.showinfo("Success", "Sample configuration saved!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save sample config: {e}")
    
    def save_system_config(self):
        """Save system configuration to YAML"""
        try:
            data = {key: var.get() for key, var in self.system_vars.items()}
            
            project_dir = self.project_path.get() if self.project_path.get() else "."
            with open(os.path.join(project_dir, "system_setup.yaml"), 'w') as f:
                yaml.dump(data, f, default_flow_style=False)
            
            messagebox.showinfo("Success", "System configuration saved!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save system config: {e}")
    
    def create_default_configs(self):
        """Create default configuration files for new project"""
        project_dir = self.project_path.get()
        
        # Default experiment config
        default_experiment = {
            'box_name': 'DefaultBox',
            'experiment_folder': 'experiment_data',
            'picture_matrix_side': 3,
            'picture_step': 10.0,
            'border_matrix_side': 2,
            'border_from_center': 15.0,
            'dish_number': 4,
            'dish_coordinates': [(0, 0, 'A1'), (1, 0, 'B1'), (0, 1, 'A2'), (1, 1, 'B2')]
        }
        
        # Default sample config
        default_sample = {
            'box_type': 'Standard',
            'col_number': 2,
            'row_number': 2,
            'x_offset': 0.0,
            'y_offset': 0.0,
            'x_dish_step': 50.0,
            'y_dish_step': 50.0
        }
        
        # Default system config
        default_system = {
            'equipment_name': 'DefaultEquipment',
            'meters_per_step_x': 0.0001,
            'meters_per_step_y': 0.0001
        }
        
        # Save defaults
        with open(os.path.join(project_dir, "experiment_setup.yaml"), 'w') as f:
            yaml.dump(default_experiment, f, default_flow_style=False)
        
        with open(os.path.join(project_dir, "box_setup.yaml"), 'w') as f:
            yaml.dump(default_sample, f, default_flow_style=False)
        
        with open(os.path.join(project_dir, "system_setup.yaml"), 'w') as f:
            yaml.dump(default_system, f, default_flow_style=False)