from .base_scheduler import BaseScheduler
from ..pcb import PCB
from typing import Optional
from collections import deque

class FCFSScheduler(BaseScheduler):
    """First-Come First-Served (Non-preemptive) Scheduler"""
    
    def __init__(self):
        super().__init__("FCFS")
        self.queue = deque()
        self.preemptive = False
    
    def add_process(self, process: PCB):
        """Add process to the end of the queue"""
        self.queue.append(process)
    
    def get_next_process(self) -> Optional[PCB]:
        """Get the process at the front of the queue"""
        if self.queue:
            return self.queue.popleft()
        return None
    
    def should_preempt(self, current_process: Optional[PCB], new_process: PCB) -> bool:
        """FCFS is non-preemptive"""
        return False