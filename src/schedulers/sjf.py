import heapq
from .base_scheduler import BaseScheduler
from ..pcb import PCB
from typing import Optional

class SJFScheduler(BaseScheduler):
    """Shortest Job First (Non-preemptive) Scheduler"""
    
    def __init__(self):
        super().__init__("SJF")
        self.heap = []  # Min-heap based on total CPU time
        self.preemptive = False
    
    def add_process(self, process: PCB):
        """Add process to heap sorted by total CPU time"""
        heapq.heappush(self.heap, (process.total_cpu_time, process.arrival_time, process.process_id, process))
    
    def get_next_process(self) -> Optional[PCB]:
        """Get the process with shortest total CPU time"""
        if self.heap:
            _, _, _, process = heapq.heappop(self.heap)
            return process
        return None
    
    @property
    def ready_queue(self):
        """Return list of processes in ready queue"""
        return [item[3] for item in self.heap]