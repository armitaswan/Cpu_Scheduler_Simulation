import heapq
from .base_scheduler import BaseScheduler
from ..pcb import PCB
from typing import Optional

class SRTFScheduler(BaseScheduler):
    """Shortest Remaining Time First (Preemptive) Scheduler"""
    
    def __init__(self):
        super().__init__("SRTF")
        self.heap = []  # Min-heap based on remaining CPU time
        self.preemptive = True
    
    def add_process(self, process: PCB):
        """Add process to heap sorted by remaining CPU time"""
        heapq.heappush(self.heap, (process.remaining_cpu_time, process.arrival_time, process.process_id, process))
    
    def get_next_process(self) -> Optional[PCB]:
        """Get the process with shortest remaining time"""
        if self.heap:
            _, _, _, process = heapq.heappop(self.heap)
            return process
        return None
    
    def should_preempt(self, current_process: Optional[PCB], new_process: PCB) -> bool:
        """Preempt if new process has shorter remaining time"""
        if not current_process:
            return False
        return new_process.remaining_cpu_time < current_process.remaining_cpu_time
    
    def on_time_quantum_expired(self, process: PCB):
        """Re-add process to heap if not completed"""
        if process.remaining_cpu_time > 0:
            self.add_process(process)
    
    @property
    def ready_queue(self):
        return [item[3] for item in self.heap]