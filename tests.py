from datetime import datetime, timedelta, timezone
from pathlib import Path
from main import validate_date, create_file

def test_validate_date_raises_for_future_race():
	"""Ensures validate_date can correctly flag dates as being in the future."""
	future = datetime.now(timezone.utc) + timedelta(days=1)
	loc = {"date_end": future.isoformat().replace("+00:00", "Z")}

	raised = False
	try:
		validate_date(loc)
	except ValueError:
		raised = True

	assert raised

def test_create_file_writes_expected_name_and_content():
	"""Ensures create_file creates and writes data provided to the file."""
	race_name = "Testing Grand Prix"
	year = 2023
	data = ["header", "row1", "row2"]
	output_path = Path("Testing_Grand_Prix_2023.txt")

	if output_path.exists():
		output_path.unlink()

	try:
		create_file(race_name, year, data)
		assert output_path.exists()
		assert output_path.read_text(encoding="utf-8") == "header\nrow1\nrow2"
	finally:
		if output_path.exists():
			output_path.unlink()

if __name__ == "__main__":
	"""Runs unit tests."""
	tests = [
		test_validate_date_raises_for_future_race,
		test_create_file_writes_expected_name_and_content,
	]

	passed = 0
	for test in tests:
		try:
			test()
			print(f"PASS: {test.__name__}")
			passed += 1
		except Exception as err:
			print(f"FAIL: {test.__name__} -> {err}")

	print(f"{passed}/{len(tests)} tests passed")