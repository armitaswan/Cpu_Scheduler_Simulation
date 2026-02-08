"""
Configuration management for the simulation
"""

import yaml
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class SimulationParams:
    """Simulation parameters"""
    time_unit: str = "ms"
    max_processes: int = 1000
    simulation_duration: int = 100000
    context_switch_time: int = 2
    log_level: str = "INFO"

@dataclass
class WorkloadParams:
    """Workload generation parameters"""
    generation_method: str = "synthetic"  # or "trace"
    num_processes: int = 500
    arrival_distribution: str = "poisson"
    arrival_lambda: float = 0.01
    cpu_burst_distribution: str = "normal"
    cpu_burst_mean: float = 50.0
    cpu_burst_std: float = 20.0
    io_burst_distribution: str = "uniform"
    io_burst_min: int = 10
    io_burst_max: int = 100
    priority_min: int = 1
    priority_max: int = 10
    workload_type: str = "mixed"  # "cpu_intensive", "io_intensive", "mixed"

@dataclass
class SchedulingParams:
    """Scheduling algorithm parameters"""
    round_robin_quantum: int = 20
    mlfq_levels: int = 3
    mlfq_quantums: list = None
    priority_aging_interval: int = 1000
    
    def __post_init__(self):
        if self.mlfq_quantums is None:
            self.mlfq_quantums = [10, 20, 40]

@dataclass
class ExperimentParams:
    """Experiment parameters"""
    baseline_num_processes: int = 500
    baseline_workload_type: str = "mixed"
    sensitivity_rr_quantums: list = None
    sensitivity_process_counts: list = None
    visualization_gantt_processes: int = 20
    visualization_save_format: str = "png"
    visualization_dpi: int = 300
    
    def __post_init__(self):
        if self.sensitivity_rr_quantums is None:
            self.sensitivity_rr_quantums = [5, 10, 20, 50, 100]
        if self.sensitivity_process_counts is None:
            self.sensitivity_process_counts = [100, 500, 1000]

class Config:
    """Configuration manager for the simulation"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.simulation = SimulationParams()
        self.workload = WorkloadParams()
        self.scheduling = SchedulingParams()
        self.experiments = ExperimentParams()
        
        if config_file:
            self.load_from_file(config_file)
    
    def load_from_file(self, config_file: str):
        """Load configuration from YAML file"""
        if not os.path.exists(config_file):
            print(f"Warning: Config file {config_file} not found. Using defaults.")
            return
        
        try:
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Update simulation parameters
            if 'simulation' in config_data:
                sim_data = config_data['simulation']
                for key, value in sim_data.items():
                    if hasattr(self.simulation, key):
                        setattr(self.simulation, key, value)
            
            # Update workload parameters
            if 'workload' in config_data:
                workload_data = config_data['workload']
                for key, value in workload_data.items():
                    if hasattr(self.workload, key):
                        setattr(self.workload, key, value)
            
            # Update scheduling parameters
            if 'scheduling' in config_data:
                sched_data = config_data['scheduling']
                for key, value in sched_data.items():
                    if hasattr(self.scheduling, key):
                        setattr(self.scheduling, key, value)
            
            # Update experiment parameters
            if 'experiments' in config_data:
                exp_data = config_data['experiments']
                for key, value in exp_data.items():
                    if hasattr(self.experiments, key):
                        setattr(self.experiments, key, value)
            
            print(f"Configuration loaded from {config_file}")
            
        except yaml.YAMLError as e:
            print(f"Error parsing config file: {e}")
        except Exception as e:
            print(f"Error loading config: {e}")
    
    def save_to_file(self, config_file: str):
        """Save current configuration to YAML file"""
        config_data = {
            'simulation': self.simulation.__dict__,
            'workload': self.workload.__dict__,
            'scheduling': self.scheduling.__dict__,
            'experiments': self.experiments.__dict__
        }
        
        # Remove None values
        for section in config_data.values():
            for key in list(section.keys()):
                if section[key] is None:
                    del section[key]
        
        try:
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            with open(config_file, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False)
            print(f"Configuration saved to {config_file}")
        except Exception as e:
            print(f"Error saving config: {e}")
    
    def get_workload_config(self) -> Dict[str, Any]:
        """Get workload configuration as dictionary"""
        return {
            'num_processes': self.workload.num_processes,
            'arrival_lambda': self.workload.arrival_lambda,
            'cpu_burst_mean': self.workload.cpu_burst_mean,
            'cpu_burst_std': self.workload.cpu_burst_std,
            'io_burst_min': self.workload.io_burst_min,
            'io_burst_max': self.workload.io_burst_max,
            'priority_min': self.workload.priority_min,
            'priority_max': self.workload.priority_max,
            'workload_type': self.workload.workload_type
        }
    
    def __str__(self):
        return (f"Config:\n"
                f"  Simulation: {self.simulation}\n"
                f"  Workload: {self.workload}\n"
                f"  Scheduling: {self.scheduling}\n"
                f"  Experiments: {self.experiments}")

# Default configuration
DEFAULT_CONFIG = Config()