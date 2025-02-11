"""Frame module for SPP"""


class Frame:
    """Class representing a single camera frame for evaluation"""

    def __init__(self, timestamp=None):
        """Initialize object attributes."""
        self.timestamp = timestamp
        self.objects_loaded = False
