class Lap:
    def __init__(self, duration=0.0, tyre_age=0):
        """Creates Lap object storing session, lap time, and age."""
        self.duration = duration
        self.tyre_age = tyre_age

    def __str__(self):
        """Returns string of Lap."""
        return f"{self.duration}s"

    def __repr__(self):
        """Returns representation of Lap."""
        return f"{self.duration}s"