import numpy as np
import random
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from .pcb import PCB

@dataclass
class WorkloadConfig:
    """Configuration for workload generation"""
    num_processes: int = 100
    arrival_lambda: float = 0.01  # for Poisson distribution
    cpu_burst_mean: float = 50.0
    cpu_burst_std: float = 20.0
    io_burst_min: int = 10
    io_burst_max: int = 100
    priority_min: int = 1
    priority_max: int = 10
    cpu_io_ratio: float = 0.7  # 70% CPU intensive
    workload_type: str = "mixed"  # "cpu_intensive", "io_intensive", "mixed"

class WorkloadGenerator:
    """Generate synthetic process workloads"""
    
    def __init__(self, config: WorkloadConfig = None):
        self.config = config or WorkloadConfig()
        self.next_pid = 1
    
    def generate_synthetic_workload(self) -> List[PCB]:
        """Generate processes using statistical distributions"""
        processes = []
        
        if self.config.workload_type == "cpu_intensive":
            cpu_io_ratio = 0.9  # 90% CPU
        elif self.config.workload_type == "io_intensive":
            cpu_io_ratio = 0.3  # 30% CPU
        else:
            cpu_io_ratio = self.config.cpu_io_ratio
        
        # Generate arrival times using Poisson process (exponential inter-arrival)
        arrival_times = np.cumsum(np.random.exponential(
            1/self.config.arrival_lambda, 
            self.config.num_processes
        )).astype(int)
        
        for i in range(self.config.num_processes):
            # Generate CPU burst time (truncated normal distribution)
            cpu_burst = int(np.random.normal(
                self.config.cpu_burst_mean, 
                self.config.cpu_burst_std
            ))
            cpu_burst = max(1, cpu_burst)  # Ensure positive
            
            # Generate I/O burst based on workload type
            if np.random.random() < cpu_io_ratio:
                # CPU-intensive process: shorter I/O bursts
                io_burst = np.random.randint(
                    self.config.io_burst_min, 
                    self.config.io_burst_max // 2
                )
            else:
                # I/O-intensive process: longer I/O bursts
                io_burst = np.random.randint(
                    self.config.io_burst_max // 2, 
                    self.config.io_burst_max
                )
            
            # Generate priority
            priority = np.random.randint(
                self.config.priority_min, 
                self.config.priority_max + 1
            )
            
            # Create PCB
            process = PCB(
                process_id=self.next_pid,
                arrival_time=int(arrival_times[i]),
                total_cpu_time=cpu_burst,
                remaining_cpu_time=cpu_burst,
                io_burst_time=io_burst,
                priority=priority
            )
            
            processes.append(process)
            self.next_pid += 1
        
        return processes
    
    def generate_from_trace(self, trace_file: str) -> List[PCB]:
        """Generate processes from a trace file"""
        processes = []
        
        try:
            with open(trace_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split(',')
                    if len(parts) < 4:
                        print(f"Warning: Invalid trace line {line_num}: {line}")
                        continue
                    
                    try:
                        pid = int(parts[0])
                        arrival = int(parts[1])
                        cpu_burst = int(parts[2])
                        io_burst = int(parts[3])
                        priority = int(parts[4]) if len(parts) > 4 else 1
                        
                        process = PCB(
                            process_id=pid,
                            arrival_time=arrival,
                            total_cpu_time=cpu_burst,
                            remaining_cpu_time=cpu_burst,
                            io_burst_time=io_burst,
                            priority=priority
                        )
                        
                        processes.append(process)
                        self.next_pid = max(self.next_pid, pid + 1)
                    
                    except ValueError as e:
                        print(f"Error parsing trace line {line_num}: {e}")
        
        except FileNotFoundError:
            print(f"Trace file not found: {trace_file}")
            return []
        
        return processes
    
    def create_sample_traces(self):
        """Create sample trace files for different workload types"""
        
        # CPU-intensive trace
        cpu_trace = []
        for i in range(100):
            arrival = i * 10
            cpu_burst = np.random.randint(80, 150)
            io_burst = np.random.randint(5, 20)
            priority = np.random.randint(1, 4)
            cpu_trace.append(f"{i+1},{arrival},{cpu_burst},{io_burst},{priority}")
        
        # I/O-intensive trace
        io_trace = []
        for i in range(100):
            arrival = i * 15
            cpu_burst = np.random.randint(5, 30)
            io_burst = np.random.randint(50, 200)
            priority = np.random.randint(1, 10)
            io_trace.append(f"{i+1},{arrival},{cpu_burst},{io_burst},{priority}")
        
        # Mixed workload trace
        mixed_trace = []
        for i in range(200):
            arrival = i * 8
            if np.random.random() < 0.5:
                cpu_burst = np.random.randint(40, 100)
                io_burst = np.random.randint(20, 60)
            else:
                cpu_burst = np.random.randint(10, 50)
                io_burst = np.random.randint(40, 120)
            priority = np.random.randint(1, 6)
            mixed_trace.append(f"{i+1},{arrival},{cpu_burst},{io_burst},{priority}")
        
        return {
            "cpu_intensive": cpu_trace,
            "io_intensive": io_trace,
            "mixed": mixed_trace
        }