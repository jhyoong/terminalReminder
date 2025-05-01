import unittest
import datetime
import reminderParser

class ReminderParserTests(unittest.TestCase):

    def test_basic_time_formats(self):
        """Test the parser with basic time formats"""
        now = datetime.datetime.now()
        today = now.date()

        test_cases = [
            # Basic time formats
            {
                "input": "call mom at 3pm",
                "expected_message": "call mom",
                "expected_time_check": lambda dt: dt.hour == 15 and dt.minute == 0
            },
            {
                "input": "meeting at 10:30am",
                "expected_message": "meeting",
                "expected_time_check": lambda dt: dt.hour == 10 and dt.minute == 30
            },
            {
                "input": "later at 11am",
                "expected_message": "Reminder",
                "expected_time_check": lambda dt: dt.hour == 11 and dt.minute == 0
            },
            {
                "input": "check oven at 5:45pm",
                "expected_message": "check oven",
                "expected_time_check": lambda dt: dt.hour == 17 and dt.minute == 45
            },

            # Time without "at"
            {
                "input": "call mom 11am",
                "expected_message": "call mom",
                "expected_time_check": lambda dt: dt.hour == 11 and dt.minute == 0
            },
            {
                "input": "meeting 10:30am",
                "expected_message": "meeting",
                "expected_time_check": lambda dt: dt.hour == 10 and dt.minute == 30
            },

            # Intervals
            {
                "input": "check email in 30 minutes",
                "expected_message": "check email",
                "expected_time_check": lambda dt: (dt - now).total_seconds() >= 29*60 and
                                                (dt - now).total_seconds() <= 31*60
            },
            {
                "input": "call back in 2 hours",
                "expected_message": "call back",
                "expected_time_check": lambda dt: (dt - now).total_seconds() >= 119*60 and
                                                (dt - now).total_seconds() <= 121*60
            },
            {
                "input": "check back in 3 days",
                "expected_message": "check back",
                "expected_time_check": lambda dt: (dt.date() - today).days == 3
            },
        ]

        self._run_test_cases(test_cases)

    def test_date_formats(self):
        """Test the parser with date formats"""
        now = datetime.datetime.now()

        test_cases = [
            # Basic date formats
            {
                "input": "meeting on 15 May",
                "expected_message": "meeting",
                "expected_time_check": lambda dt: dt.day == 15 and dt.month == 5
            },
            {
                "input": "dentist on 3rd April 2025",
                "expected_message": "dentist",
                "expected_time_check": lambda dt: dt.day == 3 and dt.month == 4 and dt.year == 2025
            },

            # Dates with times
            {
                "input": "call back on 22nd December at 3pm",
                "expected_message": "call back",
                "expected_time_check": lambda dt: dt.day == 22 and dt.month == 12 and dt.hour == 15
            }
        ]

        self._run_test_cases(test_cases)

    def test_special_timeframes(self):
        """Test the parser with special timeframes like 'tomorrow'"""
        now = datetime.datetime.now()
        today = now.date()
        tomorrow = today + datetime.timedelta(days=1)

        test_cases = [
            # Tomorrow
            {
                "input": "meeting tomorrow at 2pm",
                "expected_message": "meeting",
                "expected_time_check": lambda dt: dt.date() == tomorrow and dt.hour == 14
            },

            # Today (if time has passed, should be tomorrow)
            {
                "input": "check back today at 4:30pm",
                "expected_message": "check back",
                "expected_time_check": lambda dt: (dt.date() == today or dt.date() == tomorrow) and
                                                dt.hour == 16 and dt.minute == 30
            }
        ]

        self._run_test_cases(test_cases)

    def test_later_patterns(self):
        """Test 'later' patterns with times"""
        test_cases = [
            # Later with "at"
            {
                "input": "later at 2pm to do something",
                "expected_message": "to do something",
                "expected_time_check": lambda dt: dt.hour == 14 and dt.minute == 0
            },

            # Later without "at"
            {
                "input": "later 4pm to do nothing",
                "expected_message": "to do nothing",
                "expected_time_check": lambda dt: dt.hour == 16 and dt.minute == 0
            },

            # More variations
            {
                "input": "later at 11am check email",
                "expected_message": "check email",
                "expected_time_check": lambda dt: dt.hour == 11 and dt.minute == 0
            },
            {
                "input": "later 3pm pick up kids",
                "expected_message": "pick up kids",
                "expected_time_check": lambda dt: dt.hour == 15 and dt.minute == 0
            },

            # No message
            {
                "input": "later at 10pm",
                "expected_message": "Reminder",  # Default message when empty
                "expected_time_check": lambda dt: dt.hour == 22 and dt.minute == 0
            }
        ]

        self._run_test_cases(test_cases)

    def test_time_message_patterns(self):
        """Test time followed by message patterns"""
        test_cases = [
            # "at X message" patterns
            {
                "input": "at 3pm call mom",
                "expected_message": "call mom",
                "expected_time_check": lambda dt: dt.hour == 15 and dt.minute == 0
            },
            {
                "input": "at 11:45am dentist appointment",
                "expected_message": "dentist appointment",
                "expected_time_check": lambda dt: dt.hour == 11 and dt.minute == 45
            },

            # Without "at"
            {
                "input": "10am team meeting",
                "expected_message": "team meeting",
                "expected_time_check": lambda dt: dt.hour == 10 and dt.minute == 0
            },
            {
                "input": "2:30pm review report",
                "expected_message": "review report",
                "expected_time_check": lambda dt: dt.hour == 14 and dt.minute == 30
            }
        ]

        self._run_test_cases(test_cases)

    def _run_test_cases(self, test_cases):
        """Helper method to execute test cases"""
        for case in test_cases:
            result = reminderParser.parse_reminder(case["input"])

            # Check that parsing succeeded
            self.assertIsNotNone(result, f"Failed to parse: '{case['input']}'")

            if result:
                # Check message parsing
                result_message = result["message"].strip()
                expected_message = case["expected_message"].strip()
                self.assertEqual(result_message, expected_message,
                                f"Wrong message for '{case['input']}': expected '{expected_message}', got '{result_message}'")

                # Check time parsing using the custom check function
                trigger_time = result["trigger_time"]
                self.assertTrue(case["expected_time_check"](trigger_time),
                            f"Time check failed for '{case['input']}': got {trigger_time.strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    unittest.main()