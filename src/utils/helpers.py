"""
Helper functions for the simulation
"""

import random
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import matplotlib.colors as mcolors

def validate_positive_int(value: Any, name: str = "value") -> int:
    """Validate that a value is a positive integer"""
    try:
        int_value = int(value)
        if int_value <= 0:
            raise ValueError(f"{name} must be positive, got {value}")
        return int_value
    except (ValueError, TypeError):
        raise ValueError(f"{name} must be an integer, got {type(value).__name__}")

def validate_config(config_dict: Dict[str, Any]) -> bool:
    """Validate configuration dictionary"""
    required_fields = ['num_processes', 'arrival_lambda', 'cpu_burst_mean']
    
    for field in required_fields:
        if field not in config_dict:
            print(f"Missing required field: {field}")
            return False
    
    try:
        validate_positive_int(config_dict['num_processes'], 'num_processes')
        
        if config_dict['arrival_lambda'] <= 0:
            print("arrival_lambda must be positive")
            return False
        
        if config_dict['cpu_burst_mean'] <= 0:
            print("cpu_burst_mean must be positive")
            return False
        
        return True
    
    except ValueError as e:
        print(f"Configuration validation error: {e}")
        return False

def format_time(ms: int) -> str:
    """Format milliseconds to human-readable string"""
    if ms < 1000:
        return f"{ms} ms"
    elif ms < 60000:
        return f"{ms/1000:.1f} s"
    elif ms < 3600000:
        return f"{ms/60000:.1f} min"
    else:
        return f"{ms/3600000:.1f} hr"

def calculate_percentiles(data: List[float]) -> Dict[str, float]:
    """Calculate statistical percentiles for a dataset"""
    if not data:
        return {}
    
    data_array = np.array(data)
    
    return {
        'min': float(np.min(data_array)),
        '5th': float(np.percentile(data_array, 5)),
        '25th': float(np.percentile(data_array, 25)),
        'median': float(np.median(data_array)),
        '75th': float(np.percentile(data_array, 75)),
        '95th': float(np.percentile(data_array, 95)),
        'max': float(np.max(data_array)),
        'mean': float(np.mean(data_array)),
        'std': float(np.std(data_array))
    }

def generate_color_map(n_colors: int, colormap: str = 'tab20') -> Dict[int, str]:
    """Generate a color map for n different items"""
    cmap = plt.cm.get_cmap(colormap)
    colors = []
    
    for i in range(n_colors):
        rgba = cmap(i / max(1, n_colors - 1))
        colors.append(mcolors.to_hex(rgba))
    
    return {i: colors[i % len(colors)] for i in range(n_colors)}

def exponential_random(rate: float) -> float:
    """Generate exponential random variable with given rate"""
    if rate <= 0:
        raise ValueError("Rate must be positive")
    return random.expovariate(rate)

def normal_random(mean: float, std: float) -> float:
    """Generate normal random variable with given mean and std"""
    return random.gauss(mean, std)

def uniform_random(min_val: float, max_val: float) -> float:
    """Generate uniform random variable in [min_val, max_val]"""
    return random.uniform(min_val, max_val)

def poisson_arrival_times(rate: float, num_events: int) -> List[float]:
    """Generate arrival times using Poisson process"""
    inter_arrival_times = [exponential_random(rate) for _ in range(num_events)]
    arrival_times = np.cumsum(inter_arrival_times)
    return list(arrival_times)

def calculate_fairness_index(values: List[float]) -> float:
    """Calculate Jain's fairness index"""
    if not values:
        return 1.0
    
    sum_values = sum(values)
    sum_squares = sum(v * v for v in values)
    
    if sum_squares == 0:
        return 1.0
    
    n = len(values)
    fairness = (sum_values * sum_values) / (n * sum_squares)
    return fairness

def normalize_values(values: List[float]) -> List[float]:
    """Normalize values to [0, 1] range"""
    if not values:
        return []
    
    min_val = min(values)
    max_val = max(values)
    
    if max_val == min_val:
        return [0.5] * len(values)
    
    return [(v - min_val) / (max_val - min_val) for v in values]

def create_gantt_segments(gantt_data: List[Tuple[int, int, int]]) -> List[Dict[str, Any]]:
    """Convert raw Gantt data to segments for plotting"""
    segments = []
    
    for start, end, pid in gantt_data:
        segments.append({
            'process_id': pid,
            'start': start,
            'end': end,
            'duration': end - start
        })
    
    return segments

def merge_gantt_segments(segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merge consecutive segments of the same process"""
    if not segments:
        return []
    
    merged = []
    current = segments[0].copy()
    
    for seg in segments[1:]:
        if (seg['process_id'] == current['process_id'] and 
            seg['start'] == current['end']):
            # Merge consecutive segments
            current['end'] = seg['end']
            current['duration'] = current['end'] - current['start']
        else:
            merged.append(current)
            current = seg.copy()
    
    merged.append(current)
    return merged