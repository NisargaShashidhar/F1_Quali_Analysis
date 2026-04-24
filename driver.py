from lap import Lap

class Driver:
    def __init__(self, first_name, last_name, acronym, driver_number, team):
        """Initializes Driver object."""
        self.first_name = first_name
        self.last_name = last_name
        self.acronym = acronym
        self.driver_number = driver_number
        self.team = team
        self._stints = [] # list of tuples
        self._laps = {} # dict of laps in the form {session: [laps]}

    def add_stint(self, key, start, end, tyre_age_at_start):
        """Adds information about each lap in a stint."""
        self._stints.append(
            (
                key,
                start,
                end,
                tyre_age_at_start
            )
        )
    
    def get_stints(self):
        """Returns list of stints (tuples)."""
        return self._stints

    def add_lap(self, session, duration, age):
        """Adds information about each lap in a session."""
        if session not in self._laps:
            self._laps[session] = []
        self._laps[session].append(
            Lap(
                duration,
                age
            )
        )

    def _get_fastest_lap_time(self):
        """Finds fastest lap for the driver over a weekend."""
        fastest_lap = float("inf")
        for session_laps in self._laps.values():
            for lap in session_laps:
                if lap.duration < fastest_lap:
                    fastest_lap = lap.duration
        if fastest_lap == float("inf"):
            return 0
        return fastest_lap

    def _is_push_lap(self, fastest_lap, lap):
        """Determines if the lap is a 'push' lap or a warmup/cooldown lap."""
        if lap.duration < fastest_lap + 10:
            return True
        return False

    def _get_weight(self, lap):
        """Weights laps based on tyre age."""
        if lap.tyre_age < 2:
            return 0.9
        elif lap.tyre_age < 5:
            return 1
        elif lap.tyre_age < 15:
            return 0.95
        else: 
            return 0.9

    def get_average(self):
        """Gets weighted average for push laps."""
        fastest_lap = self._get_fastest_lap_time()
        push_laps = [lap for session_laps in self._laps.values() for lap in session_laps if self._is_push_lap(fastest_lap, lap)]
        if not push_laps:
            return 0
        return sum(lap.duration*self._get_weight(lap) for lap in push_laps) / len(push_laps)
    
    def get_average_by_session(self):
        """Gets weighted average for push laps in each session."""
        fastest_lap = self._get_fastest_lap_time()
        averages = {}
        for session, laps in self._laps.items():
            push_laps = [lap for lap in laps if self._is_push_lap(fastest_lap, lap)]
            if push_laps:
                averages[session] = sum(lap.duration*self._get_weight(lap) for lap in push_laps) / len(push_laps)
            else:
                averages[session] = 0
        return averages
    
    def __str__(self):
        """Returns string of Driver."""
        return f"{self.acronym}"

    def __repr__(self):
        """Returns representation of Driver."""
        return f"{self.acronym}"
    
    def __eq__(self, other):
        """Returns equality of drivers based on average lap time."""
        if not isinstance(other, Driver):
            return NotImplemented
        return self.get_average() == other.get_average()

    def __lt__(self, other):
        """Returns less than (<) of drivers based on average lap time."""
        if not isinstance(other, Driver):
            return NotImplemented
        return self.get_average() < other.get_average()

    def __le__(self, other):
        """Returns less than/equal to (<=) of drivers based on average lap time."""
        if not isinstance(other, Driver):
            return NotImplemented
        return self.get_average() <= other.get_average()

    def __gt__(self, other):
        """Returns greater than (>) of drivers based on average lap time."""
        if not isinstance(other, Driver):
            return NotImplemented
        return self.get_average() > other.get_average()

    def __ge__(self, other):
        """Returns greater than/equal to (>=) of drivers based on average lap time."""
        if not isinstance(other, Driver):
            return NotImplemented
        return self.get_average() >= other.get_average()

    def __ne__(self, other):
        """Returns inequality (!=) of drivers based on average lap time."""
        if not isinstance(other, Driver):
            return NotImplemented
        return self.get_average() != other.get_average()