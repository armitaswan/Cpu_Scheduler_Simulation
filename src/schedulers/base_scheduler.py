from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from ..pcb import PCB

class BaseScheduler(ABC):
    """Abstract base class for all schedulers"""
    
    def __init__(self, name: str = "BaseScheduler"):
        self.name = name
        self.ready_queue = []
        self.preemptive = False
        self.stats = {
            "context_switches": 0,
            "preemptions": 0,
            "idle_time": 0
        }
    
    @abstractmethod
    def add_process(self, process: PCB):
        """Add a process to the scheduler's ready queue"""
        pass
    
    @abstractmethod
    def get_next_process(self) -> Optional[PCB]:
        """Get the next process to execute"""
        pass
    
    def is_preemptive(self) -> bool:
        return self.preemptive
    
    def should_preempt(self, current_process: Optional[PCB], new_process: PCB) -> bool:
        """Determine if new process should preempt current process"""
        return False
    
    def on_process_completion(self, process: PCB):
        """Called when a process completes execution"""
        pass
    
    def on_time_quantum_expired(self, process: PCB):
        """Called when a process's time quantum expires"""
        pass
    
    def update_waiting_times(self, current_time: int, last_update_time: int):
        """Update waiting times for all processes in ready queue"""
        time_diff = current_time - last_update_time
        for process in self.ready_queue:
            if process.state.name == "READY":
                process.total_waiting_time += time_diff
    
    def get_queue_length(self) -> int:
        return len(self.ready_queue)
    
    def is_empty(self) -> bool:
        return len(self.ready_queue) == 0
    
    def clear(self):
        self.ready_queue.clear()
        self.stats = {
            "context_switches": 0,
            "preemptions": 0,
            "idle_time": 0
        }
    
    def __str__(self):
        return f"{self.name}(Processes: {len(self.ready_queue)})"