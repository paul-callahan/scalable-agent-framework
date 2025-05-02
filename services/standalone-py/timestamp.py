from dataclasses import dataclass


@dataclass
class Timestamp:
    """Represents a point in time with nanosecond precision"""
    
    # Seconds since the Unix epoch
    seconds: int
    
    # Nanoseconds of the second
    nanos: int
    
    def __post_init__(self):
        """Validate timestamp after initialization"""
        if self.seconds < 0:
            raise ValueError("seconds cannot be negative")
        if self.nanos < 0 or self.nanos >= 1_000_000_000:
            raise ValueError("nanos must be between 0 and 999,999,999") 