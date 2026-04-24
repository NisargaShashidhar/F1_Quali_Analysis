from urllib.request import urlopen
from urllib.error import URLError, HTTPError
import json
import time
import random
from datetime import datetime
from driver import Driver

REQUESTS_PER_SECOND = 3
MIN_INTERVAL = 1.0 / REQUESTS_PER_SECOND
_last_request_time = 0.0

def validate_date(loc):
    """Checks to see if selected meeting has not yet occurred."""
    date_end_str = loc["date_end"]
    date_end = datetime.fromisoformat(date_end_str.replace('Z', '+00:00'))

    if datetime.now(date_end.tzinfo) > date_end:
        return
    else:
        raise ValueError("Value ERR: Please select a completed Grand Prix.")
    

def fetch_json_with_retry(url, max_retries=6, base_delay=0.5):
    """Rate-limited fetch with retry/quit for 429 and other URL errors."""
    global _last_request_time

    for attempt in range(max_retries):
        try:
            # Inline rate limit: <= 3 requests/second
            now = time.monotonic()
            wait = MIN_INTERVAL - (now - _last_request_time)
            if wait > 0:
                time.sleep(wait)
            _last_request_time = time.monotonic()

            with urlopen(url, timeout=20) as response:
                return json.loads(response.read().decode("utf-8"))

        except HTTPError as err:
            if err.code == 429:
                retry_after = err.headers.get("Retry-After")
                if retry_after and retry_after.isdigit():
                    wait_seconds = float(retry_after)
                else:
                    wait_seconds = base_delay * (2 ** attempt) + random.uniform(0, 0.25)
                time.sleep(wait_seconds)
                continue
            raise

        except URLError:
            wait_seconds = base_delay * (2 ** attempt) + random.uniform(0, 0.25)
            time.sleep(wait_seconds)

    raise RuntimeError(f"Failed after {max_retries} retries: {url}")


def get_driver_by_number(drivers, driver_number):
    """Return the matching Driver object for a driver number."""
    for d in drivers:
        if d.driver_number == driver_number:
            return d
    return None

def create_file(race_name, year, data):
    """Saves the generated predictions to a txt file."""
    safe_race_name = str(race_name).strip().replace(" ", "_")
    filename = f"{safe_race_name}_{year}.txt"

    if isinstance(data, list):
        content = "\n".join(str(item) for item in data)
    else:
        content = str(data)

    with open(filename, "w", encoding="utf-8") as out_file:
        out_file.write(content)

if __name__ == "__main__":
    """Predicts which drivers will be fastest in qualifying based on OpenF1 data."""
    
    current_year = datetime.today().year

    while True:
        try:
            year_str = input(f"Please enter a year between 2023 and {current_year}: ")

            if not year_str.isnumeric():
                raise ValueError("Value ERR: Please enter only integer values.")
    
            year = int(year_str)
            if year < 2023 or year > current_year:
                raise ValueError(f"Value ERR: Please enter a year between 2023 and {current_year}.")
            
            break
            
        except ValueError as err:
            print(err)
    
    try:
        meeting_data = fetch_json_with_retry(f"https://api.openf1.org/v1/meetings?year={year}")
    except HTTPError as err:
        print(f"Meeting HTTP ERR: {err.code} {err.reason}")
    except URLError as err:
        print(f"Meeting URL ERR: {err.reason}")

    meetings = []
    for meeting in meeting_data:
        if meeting.get("is_cancelled", False) == False:
            if meeting.get("meeting_name", "") != "Pre-Season Testing":
                meetings.append({
                    "meeting_name": meeting.get("meeting_name", ""),
                    "meeting_key": meeting.get("meeting_key", ""),
                    "country_code": meeting.get("country_code", ""),
                    "location": meeting.get("location", ""),
                    "date_end": meeting.get("date_end", "")
                })
    meetings_by_code = {}
    for m in meetings:
        code = m["country_code"].upper()
        if code not in meetings_by_code:
            meetings_by_code[code] = []
        meetings_by_code[code].append(m)
    meeting_codes = set(meetings_by_code.keys())

    for m in meetings:
        print(f"{m['country_code']} | {m['meeting_name']}")
    
    while True:
        try:
            loc_str = input("Enter the 3 letter code of the desired Grand Prix: ").strip().upper()

            if len(loc_str) != 3 or not loc_str.isalpha():
                raise ValueError("Value ERR: Please enter a valid 3-letter country code.")

            if loc_str not in meeting_codes:
                raise ValueError("Value ERR: No Grand Prix found for that country code.")

            matching_meetings = meetings_by_code[loc_str]

            if len(matching_meetings) == 1:
                loc = matching_meetings[0]
            else:
                print("Multiple races found for that country code. Please choose one:")
                for meeting in matching_meetings:
                    print(f"{meeting['meeting_name']} ({meeting['location']})")

                while True:
                    choice_str = input("Enter the race location: ").strip().lower()
                    loc = next(
                        (
                            meeting for meeting in matching_meetings
                            if meeting.get("location", "").strip().lower() == choice_str
                        ),
                        None,
                    )

                    if loc is None:
                        print("Value ERR: Please enter a valid race location from the list.")
                        continue

                    break
            
            print(f"You selected the {year} {loc['meeting_name']}.")
            
            validate_date(loc)
            break
            
        except ValueError as err:
            print(err)

    try:
        session_data = fetch_json_with_retry(
            f"https://api.openf1.org/v1/sessions?meeting_key={loc['meeting_key']}"
            + "&session_type=Practice"
        )
    except HTTPError as err:
        print(f"Session HTTP ERR: {err.code} {err.reason}")
    except URLError as err:
        print(f"Session URL ERR: {err.reason}")

    practice_sessions = []
    for session in session_data:
        if session.get("is_cancelled", False) == False:
            if session.get("session_type", "") == "Practice":
                practice_sessions.append({
                    "session_name": session.get("session_name", ""),
                    "session_key": session.get("session_key", ""),
                })

    
    drivers = []

    if not practice_sessions or len(practice_sessions) == 0:
        print("There are no practice sessions for this weekend.")
        # break
    else:
        last_session = practice_sessions[len(practice_sessions)-1]
        try:
            driver_data = fetch_json_with_retry(f"https://api.openf1.org/v1/drivers?" +
                                f"session_key={last_session['session_key']}")

            for d in driver_data:
                driver_number = d.get("driver_number")
                drivers.append(
                    Driver(
                        first_name=d.get("first_name"),
                        last_name=d.get("last_name"),
                        acronym=d.get("name_acronym"),
                        driver_number=d.get("driver_number"),
                        team=d.get("team_name")
                    )
                )
        except HTTPError as err:
            print(f"Driver HTTP ERR: {err.code} {err.reason}")
        except URLError as err:
            print(f"Driver URL ERR: {err.reason}")
   
    for s in practice_sessions:
        try:
            stint_data = fetch_json_with_retry(
                f"https://api.openf1.org/v1/stints?session_key={s['session_key']}"
            )
            for stint in stint_data:
                if stint.get("compound") == "SOFT":
                    driver_number = stint.get("driver_number")
                    driver = next((d for d in drivers if d.driver_number == driver_number), None)
                    if driver:
                        driver.add_stint(
                            s["session_key"],
                            int(stint.get("lap_start")),
                            int(stint.get("lap_end")),
                            int(stint.get("tyre_age_at_start"))
                        )
        except HTTPError as err:
            print(f"Stint HTTP ERR: {err.code} {err.reason}")
        except URLError as err:
            print(f"Stint URL ERR: {err.reason}")
        except ValueError as err:
            print(f"Stint Value ERR: {err.reason}")

    drivers_by_number = {}
    for d in drivers:
        drivers_by_number[d.driver_number] = d

    stints_by_session_driver = {}
    for d in drivers:
        for s_key, start, end, start_age in d.get_stints():
            key = (s_key, d.driver_number)
            if key not in stints_by_session_driver:
                stints_by_session_driver[key] = []
            stints_by_session_driver[key].append((start, end, start_age))

    for s in practice_sessions:
        s_key = s["session_key"]
        try:
            lap_data = fetch_json_with_retry(
                f"https://api.openf1.org/v1/laps?session_key={s_key}"
            )

            for lap in sorted(lap_data, key=lambda x: x.get("lap_number", 0)):
                driver_number = lap.get("driver_number")
                lap_num = lap.get("lap_number")
                lap_duration = lap.get("lap_duration")

                if driver_number is None or lap_num is None or lap_duration is None:
                    continue

                if lap.get("is_pit_out_lap", False):
                    continue

                driver = drivers_by_number.get(driver_number)
                if driver is None:
                    continue

                lap_num = int(lap_num)
                stint_key = (s_key, driver_number)
                stints = stints_by_session_driver.get(stint_key, [])

                for start, end, start_age in stints:
                    if start <= lap_num <= end:
                        tyre_age = start_age + (lap_num - start)
                        driver.add_lap(
                            s_key,
                            float(lap_duration),
                            tyre_age
                        )
                        break

        except HTTPError as err:
            print(f"Lap HTTP ERR: {err.code} {err.reason} for session {s_key}")
        except URLError as err:
            print(f"Lap URL ERR: {err.reason} for session {s_key}")
        except ValueError as err:
            print(f"Lap Value ERR: {err} for session {s_key}")

    try:
        quali_data = fetch_json_with_retry(
            f"https://api.openf1.org/v1/sessions?meeting_key={loc['meeting_key']}" 
            + "&session_type=Qualifying"
        )
    except HTTPError as err:
        print(f"Session HTTP ERR: {err.code} {err.reason}")
    except URLError as err:
        print(f"Session URL ERR: {err.reason}")

    qualifying = {
        "session_name": quali_data[0].get("session_name", ""),
        "session_key": quali_data[0].get("session_key", ""),
    }

    try:
        quali_data = fetch_json_with_retry(
            f"https://api.openf1.org/v1/sessions?meeting_key=" 
            + f"{loc['meeting_key']}&session_type=Qualifying"
        )
    except HTTPError as err:
        print(f"Session HTTP ERR: {err.code} {err.reason}")
    except URLError as err:
        print(f"Session URL ERR: {err.reason}")

    qualifying = {
        "session_name": quali_data[0].get("session_name", ""),
        "session_key": quali_data[0].get("session_key", ""),
    }

    quali_exists = False if qualifying is None else True
    
    starting_grid = []
    if quali_exists:
        try:
            result_data = fetch_json_with_retry(
                f"https://api.openf1.org/v1/session_result?session_key=" 
                + f"{qualifying['session_key']}"
            )
        except HTTPError as err:
            print(f"Session HTTP ERR: {err.code} {err.reason}")
        except URLError as err:
            print(f"Session URL ERR: {err.reason}")

        for place in result_data:
            starting_grid.append(
                {
                    "driver": get_driver_by_number(drivers, place.get("driver_number")),
                    "lap_times": place.get("duration")
                }
            )

    prediction_output = []
    
    session_headers = "\t| ".join(s["session_name"] for s in practice_sessions)
    header = f"Driver\t| {session_headers}\t| Average"
    if quali_exists:
        header += f"\t| Result\t| Lap Time"
    print(header)
    
    session_headers = "| ".join(s["session_name"] for s in practice_sessions)
    header = f"Driver\t| {session_headers}| Average"
    if quali_exists:
        header += f"\t| Result\t| Lap Time"
    prediction_output.append(header)

    sorted_drivers = sorted(drivers)
    for i, d in enumerate(sorted_drivers, start=1):
        averages_by_session = d.get_average_by_session()
        averages = []
        for s in practice_sessions:
            average = averages_by_session.get(s["session_key"], 0)
            averages.append("No Time" if average == 0 else f"{average:.3f}s")
        averages.append("No Time" if d.get_average() == 0 else f"{d.get_average():.3f}s")
        averages = "\t| ".join(averages)

        display_str = f"{i}. {d}\t| {averages}"
        if quali_exists and i <= len(starting_grid):
            display_str += f"\t| {starting_grid[i - 1].get('driver')}"
            last_lap = "No Time"
            lap_times = starting_grid[i - 1].get("lap_times")
            if lap_times:
                for lap_time in reversed(lap_times):
                    if lap_time is not None:
                        last_lap = f"{lap_time}s"
                        break
            display_str += f"\t\t| {last_lap}"
        prediction_output.append(display_str)
        print(display_str)

    while True:
        try:
            file_req_str = input(f"Would you like to save this as a file? (y/n)").lower()

            if not file_req_str.isalpha() or len(file_req_str) != 1:
                raise ValueError("Value ERR: Please enter either 'y' or 'n'.")
    
            if file_req_str == "y":
                create_file(loc.get("meeting_name"), year, prediction_output)
                print("Prediction Data Saved.")
            elif file_req_str == "n":
                break
            else:
                raise ValueError("Value ERR: Please enter either 'y' or 'n'.")
            break
            
        except ValueError as err:
            print(err)