from dataclasses import dataclass


@dataclass
class Duration:
    """Represents a span of time"""
    
    # Total seconds
    seconds: int
    
    # Nanoseconds of the second
    nanos: int
    
    def __post_init__(self):
        """Validate duration after initialization"""
        if self.seconds < 0:
            raise ValueError("seconds cannot be negative")
        if self.nanos < 0 or self.nanos >= 1_000_000_000:
            raise ValueError("nanos must be between 0 and 999,999,999") 