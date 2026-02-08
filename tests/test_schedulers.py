#!/usr/bin/env python3
"""
Unit tests for scheduling algorithms
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
import heapq
from src.pcb import PCB
from src.schedulers.fcfs import FCFSScheduler
from src.schedulers.sjf import SJFScheduler
from src.schedulers.srtf import SRTFScheduler
from src.schedulers.round_robin import RoundRobinScheduler
from src.schedulers.priority import PriorityScheduler
from src.schedulers.mlfq import MLFQScheduler

class TestFCFSScheduler(unittest.TestCase):
    """Test FCFS scheduler"""
    
    def setUp(self):
        self.scheduler = FCFSScheduler()
    
    def test_add_process(self):
        """Test adding processes to FCFS"""
        process1 = PCB(1, 0, 50, 50, 20, 1)
        process2 = PCB(2, 10, 30, 30, 15, 2)
        
        self.scheduler.add_process(process1)
        self.scheduler.add_process(process2)
        
        self.assertEqual(self.scheduler.get_queue_length(), 2)
    
    def test_get_next_process(self):
        """Test getting next process from FCFS"""
        process1 = PCB(1, 0, 50, 50, 20, 1)
        process2 = PCB(2, 10, 30, 30, 15, 2)
        
        self.scheduler.add_process(process1)
        self.scheduler.add_process(process2)
        
        # Should get processes in FIFO order
        self.assertEqual(self.scheduler.get_next_process().process_id, 1)
        self.assertEqual(self.scheduler.get_next_process().process_id, 2)
        self.assertIsNone(self.scheduler.get_next_process())
    
    def test_is_preemptive(self):
        """Test FCFS preemption property"""
        self.assertFalse(self.scheduler.is_preemptive())
    
    def test_should_preempt(self):
        """Test FCFS preemption decision"""
        current = PCB(1, 0, 50, 50, 20, 1)
        new = PCB(2, 10, 30, 30, 15, 2)
        
        # FCFS should never preempt
        self.assertFalse(self.scheduler.should_preempt(current, new))
        self.assertFalse(self.scheduler.should_preempt(None, new))

class TestSJFScheduler(unittest.TestCase):
    """Test SJF scheduler"""
    
    def setUp(self):
        self.scheduler = SJFScheduler()
    
    def test_add_process(self):
        """Test adding processes to SJF"""
        process1 = PCB(1, 0, 50, 50, 20, 1)  # Longer job
        process2 = PCB(2, 10, 30, 30, 15, 2)  # Shorter job
        
        self.scheduler.add_process(process1)
        self.scheduler.add_process(process2)
        
        self.assertEqual(self.scheduler.get_queue_length(), 2)
    
    def test_get_next_process(self):
        """Test SJF scheduling order (shortest first)"""
        process1 = PCB(1, 0, 50, 50, 20, 1)  # 50ms
        process2 = PCB(2, 10, 30, 30, 15, 2)  # 30ms
        process3 = PCB(3, 20, 40, 40, 25, 3)  # 40ms
        
        # Add in different order
        self.scheduler.add_process(process1)
        self.scheduler.add_process(process3)
        self.scheduler.add_process(process2)
        
        # Should get shortest job first (process2)
        self.assertEqual(self.scheduler.get_next_process().process_id, 2)
        # Then next shortest (process3)
        self.assertEqual(self.scheduler.get_next_process().process_id, 3)
        # Then longest (process1)
        self.assertEqual(self.scheduler.get_next_process().process_id, 1)

class TestSRTFScheduler(unittest.TestCase):
    """Test SRTF (preemptive SJF) scheduler"""
    
    def setUp(self):
        self.scheduler = SRTFScheduler()
    
    def test_add_process(self):
        """Test adding processes to SRTF"""
        process1 = PCB(1, 0, 50, 50, 20, 1)
        process2 = PCB(2, 10, 30, 30, 15, 2)
        
        self.scheduler.add_process(process1)
        self.scheduler.add_process(process2)
        
        self.assertEqual(self.scheduler.get_queue_length(), 2)
    
    def test_should_preempt(self):
        """Test SRTF preemption decision"""
        # Current process with 40ms remaining
        current = PCB(1, 0, 50, 40, 20, 1)
        
        # New process with 30ms remaining (shorter)
        new1 = PCB(2, 10, 30, 30, 15, 2)
        
        # New process with 50ms remaining (longer)
        new2 = PCB(3, 20, 60, 50, 25, 3)
        
        # Should preempt when new process has shorter remaining time
        self.assertTrue(self.scheduler.should_preempt(current, new1))
        
        # Should not preempt when new process has longer remaining time
        self.assertFalse(self.scheduler.should_preempt(current, new2))
        
        # Should not preempt when no current process
        self.assertFalse(self.scheduler.should_preempt(None, new1))

class TestRoundRobinScheduler(unittest.TestCase):
    """Test Round Robin scheduler"""
    
    def setUp(self):
        self.scheduler = RoundRobinScheduler(time_quantum=20)
    
    def test_time_quantum(self):
        """Test time quantum property"""
        self.assertEqual(self.scheduler.get_time_quantum(), 20)
    
    def test_on_time_quantum_expired(self):
        """Test handling of time quantum expiration"""
        process = PCB(1, 0, 50, 30, 20, 1)  # 30ms remaining
        
        self.scheduler.add_process(process)
        self.scheduler.on_time_quantum_expired(process)
        
        # Process should be re-added to queue
        self.assertEqual(self.scheduler.get_queue_length(), 1)
        self.assertEqual(self.scheduler.stats["preemptions"], 1)

class TestPriorityScheduler(unittest.TestCase):
    """Test Priority scheduler"""
    
    def test_preemptive_priority(self):
        """Test preemptive priority scheduling"""
        scheduler = PriorityScheduler(preemptive=True)
        
        # Current process with priority 3
        current = PCB(1, 0, 50, 50, 20, 3)
        
        # New process with higher priority (lower number)
        new1 = PCB(2, 10, 30, 30, 15, 1)
        
        # New process with lower priority (higher number)
        new2 = PCB(3, 20, 40, 40, 25, 5)
        
        # Should preempt when new process has higher priority
        self.assertTrue(scheduler.should_preempt(current, new1))
        
        # Should not preempt when new process has lower priority
        self.assertFalse(scheduler.should_preempt(current, new2))
    
    def test_non_preemptive_priority(self):
        """Test non-preemptive priority scheduling"""
        scheduler = PriorityScheduler(preemptive=False)
        
        current = PCB(1, 0, 50, 50, 20, 3)
        new = PCB(2, 10, 30, 30, 15, 1)
        
        # Should not preempt even with higher priority
        self.assertFalse(scheduler.should_preempt(current, new))
    
    def test_apply_aging(self):
        """Test priority aging mechanism"""
        scheduler = PriorityScheduler(preemptive=True, aging_interval=1000)
        
        # Add a process with low priority
        process = PCB(1, 0, 100, 100, 20, 10)  # Priority 10 (low)
        scheduler.add_process(process)
        
        # Apply aging after enough time
        scheduler.apply_aging(current_time=1500)
        
        # Process priority should be reduced (improved)
        self.assertEqual(process.priority, 9)

class TestMLFQScheduler(unittest.TestCase):
    """Test Multilevel Feedback Queue scheduler"""
    
    def setUp(self):
        self.scheduler = MLFQScheduler(num_queues=3, time_quanta=[10, 20, 40])
    
    def test_initial_queue_assignment(self):
        """Test that new processes go to highest priority queue"""
        process = PCB(1, 0, 50, 50, 20, 1)
        self.scheduler.add_process(process)
        
        self.assertEqual(process.current_queue_level, 0)
        self.assertEqual(self.scheduler.queues[0][0].process_id, 1)
    
    def test_get_time_quantum_for_process(self):
        """Test time quantum assignment based on queue level"""
        process = PCB(1, 0, 50, 50, 20, 1)
        
        # Level 0 should get quantum 10
        process.current_queue_level = 0
        self.assertEqual(self.scheduler.get_time_quantum_for_process(process), 10)
        
        # Level 1 should get quantum 20
        process.current_queue_level = 1
        self.assertEqual(self.scheduler.get_time_quantum_for_process(process), 20)
        
        # Level 2 should get quantum 40
        process.current_queue_level = 2
        self.assertEqual(self.scheduler.get_time_quantum_for_process(process), 40)
        
        # Level beyond available quanta should get last quantum
        process.current_queue_level = 5
        self.assertEqual(self.scheduler.get_time_quantum_for_process(process), 40)
    
    def test_demotion(self):
        """Test process demotion after using time quantum"""
        process = PCB(1, 0, 100, 100, 20, 1)
        self.scheduler.add_process(process)
        
        # Simulate multiple runs at same level
        self.scheduler.process_counts[process.process_id] = 2
        
        # Time quantum expires, should demote to next level
        self.scheduler.on_time_quantum_expired(process)
        
        self.assertEqual(process.current_queue_level, 1)
        self.assertEqual(len(self.scheduler.queues[1]), 1)
    
    def test_priority_boost(self):
        """Test periodic priority boost"""
        # Add process to low priority queue
        process = PCB(1, 0, 50, 50, 20, 1)
        process.current_queue_level = 2
        self.scheduler.queues[2].append(process)
        
        # Apply boost
        self.scheduler.apply_priority_boost(current_time=6000)
        
        # Process should be moved to queue 0
        self.assertEqual(process.current_queue_level, 0)
        self.assertEqual(len(self.scheduler.queues[0]), 1)
        self.assertEqual(len(self.scheduler.queues[2]), 0)

def run_all_scheduler_tests():
    """Run all scheduler tests"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestFCFSScheduler))
    suite.addTests(loader.loadTestsFromTestCase(TestSJFScheduler))
    suite.addTests(loader.loadTestsFromTestCase(TestSRTFScheduler))
    suite.addTests(loader.loadTestsFromTestCase(TestRoundRobinScheduler))
    suite.addTests(loader.loadTestsFromTestCase(TestPriorityScheduler))
    suite.addTests(loader.loadTestsFromTestCase(TestMLFQScheduler))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_all_scheduler_tests()
    sys.exit(0 if success else 1)