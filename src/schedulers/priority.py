import heapq
from .base_scheduler import BaseScheduler
from ..pcb import PCB
from typing import Optional

class PriorityScheduler(BaseScheduler):
    """Priority Scheduling with Aging (Both preemptive and non-preemptive)"""
    
    def __init__(self, preemptive: bool = True, aging_interval: int = 1000):
        mode = "Preemptive" if preemptive else "Non-preemptive"
        super().__init__(f"Priority({mode})")
        self.heap = []  # Min-heap (lower priority number = higher priority)
        self.preemptive = preemptive
        self.aging_interval = aging_interval
        self.last_aging_time = 0
    
    def add_process(self, process: PCB):
        """Add process to heap sorted by priority, then arrival time"""
        heapq.heappush(self.heap, (process.priority, process.arrival_time, process.process_id, process))
    
    def get_next_process(self) -> Optional[PCB]:
        """Get the process with highest priority (lowest number)"""
        if self.heap:
            _, _, _, process = heapq.heappop(self.heap)
            return process
        return None
    
    def should_preempt(self, current_process: Optional[PCB], new_process: PCB) -> bool:
        """Preempt if new process has higher priority (lower number)"""
        if not current_process or not self.preemptive:
            return False
        return new_process.priority < current_process.priority
    
    def apply_aging(self, current_time: int):
        """Age processes to prevent starvation"""
        if current_time - self.last_aging_time >= self.aging_interval:
            self.last_aging_time = current_time
            
            # Create new heap with aged priorities
            new_heap = []
            for priority, arrival_time, pid, process in self.heap:
                # Age the process
                if process.age_priority(current_time, self.aging_interval):
                    # Priority changed, update heap entry
                    heapq.heappush(new_heap, (process.priority, arrival_time, pid, process))
                else:
                    # Priority unchanged, keep original entry
                    heapq.heappush(new_heap, (priority, arrival_time, pid, process))
            
            self.heap = new_heap
    
    @property
    def ready_queue(self):
        return [item[3] for item in self.heap]