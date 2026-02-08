from enum import Enum
from dataclasses import dataclass, field
from typing import Optional

class ProcessState(Enum):
    """Process states for the simulation"""
    NEW = "NEW"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"  # For I/O
    TERMINATED = "TERMINATED"

@dataclass
class PCB:
    """Process Control Block"""
    # Core attributes
    process_id: int
    arrival_time: int
    total_cpu_time: int  # Original total CPU burst needed
    remaining_cpu_time: int  # Remaining CPU time
    io_burst_time: int  # I/O burst duration
    priority: int = 1
    
    # Dynamic state
    state: ProcessState = ProcessState.NEW
    current_queue_level: int = 0  # For MLFQ
    
    # Timing statistics
    start_time: Optional[int] = None
    completion_time: Optional[int] = None
    first_run_time: Optional[int] = None
    last_run_time: Optional[int] = None
    total_waiting_time: int = 0
    total_io_time: int = 0
    
    # For preemption tracking
    preempted: bool = False
    context_switches: int = 0
    
    # Performance metrics (calculated after completion)
    turnaround_time: Optional[int] = None
    waiting_time: Optional[int] = None
    response_time: Optional[int] = None
    
    def __str__(self):
        return f"P{self.process_id}[Arr:{self.arrival_time}, CPU:{self.total_cpu_time}, Pri:{self.priority}]"
    
    def calculate_metrics(self):
        """Calculate performance metrics after process completion"""
        if self.completion_time is not None:
            self.turnaround_time = self.completion_time - self.arrival_time
            self.waiting_time = self.total_waiting_time
            self.response_time = self.first_run_time - self.arrival_time if self.first_run_time else 0
    
    def age_priority(self, current_time, aging_interval=1000):
        """Age the priority to prevent starvation"""
        if current_time - self.arrival_time > aging_interval and self.priority > 1:
            self.priority -= 1
            return True
        return False
    
    def execute(self, time_slice: Optional[int] = None):
        """
        Execute the process for given time slice or until completion
        Returns: (time_used, completed, remaining_time)
        """
        if time_slice is None:
            # Execute until completion
            time_used = self.remaining_cpu_time
            self.remaining_cpu_time = 0
            return time_used, True, 0
        
        # Execute with time quantum
        if self.remaining_cpu_time <= time_slice:
            time_used = self.remaining_cpu_time
            self.remaining_cpu_time = 0
            return time_used, True, 0
        else:
            self.remaining_cpu_time -= time_slice
            return time_slice, False, self.remaining_cpu_time