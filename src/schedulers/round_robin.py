from .base_scheduler import BaseScheduler
from ..pcb import PCB
from typing import Optional
from collections import deque

class RoundRobinScheduler(BaseScheduler):
    """Round Robin Scheduler with configurable time quantum"""
    
    def __init__(self, time_quantum: int = 20):
        super().__init__(f"RR(q={time_quantum})")
        self.queue = deque()
        self.time_quantum = time_quantum
        self.preemptive = True
    
    def add_process(self, process: PCB):
        """Add process to the end of the queue"""
        self.queue.append(process)
    
    def get_next_process(self) -> Optional[PCB]:
        """Get the process at the front of the queue"""
        if self.queue:
            return self.queue.popleft()
        return None
    
    def should_preempt(self, current_process: Optional[PCB], new_process: PCB) -> bool:
        """Round Robin doesn't preempt based on priority, only on time quantum"""
        return False
    
    def on_time_quantum_expired(self, process: PCB):
        """Re-add process to end of queue if not completed"""
        if process.remaining_cpu_time > 0:
            self.queue.append(process)
            self.stats["preemptions"] += 1
    
    def get_time_quantum(self) -> int:
        return self.time_quantum