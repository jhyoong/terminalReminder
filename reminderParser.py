import re
import datetime
import dateparser
import logging

logger = logging.getLogger('remindme')

class ReminderParser:
    """
    A more structured approach to parsing reminder text with time expressions.
    This class extracts time components, processes keywords, and determines
    both the trigger datetime and the actual reminder message.
    """

    # Time component patterns
    TIME_PATTERNS = {
        'specific_time': r'(\d{1,2}(?::\d{2})?\s*(?:am|pm))',  # 3pm, 11:30am
        'time_with_at': r'at\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm))',  # at 3pm
        'interval': r'in\s+(\d+)\s*(second|minute|hour|day|week|month|year|sec|min|hr|s|m|h|d|w|y)s?',  # in 30 minutes
        'date': r'(\d{1,2}(?:st|nd|rd|th)?)\s+(?:of\s+)?(January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)(?:\s+(\d{4}))?',  # 15th April, 3 Jan 2025
        'today': r'today',
        'tomorrow': r'tomorrow',
        'next_week': r'next\s+week',
        'next_month': r'next\s+month'
    }

    # Special keyword patterns
    KEYWORDS = {
        'later': r'later',
        'at': r'at\b',
        'on': r'on\b',
        'by': r'by\b',
        'before': r'before\b'
    }

    # Time unit mapping for interval calculations
    TIME_UNITS = {
        'second': 1, 'sec': 1, 's': 1,
        'minute': 60, 'min': 60, 'm': 60,
        'hour': 3600, 'hr': 3600, 'h': 3600,
        'day': 86400, 'd': 86400,
        'week': 604800, 'w': 604800,
        'month': 2592000,  # Approximate
        'year': 31536000   # Approximate
    }

    def __init__(self, text):
        """Initialize with the text to parse."""
        self.original_text = text.strip()
        self.text = text.lower().strip()
        self.time_components = {}
        self.keywords = {}
        self.message = None
        self.trigger_time = None

    def parse(self):
        """Main parsing method that orchestrates the extraction process."""
        # Step 1: Extract all time components
        self._extract_time_components()
        logger.debug(f"Extracted time components: {self.time_components}")

        # Step 2: Identify special keywords
        self._identify_keywords()
        logger.debug(f"Identified keywords: {self.keywords}")

        # Step 3: Determine the trigger time
        self._determine_trigger_time()

        # Step 4: Extract the message after removing time components
        self._extract_message()

        return {
            'trigger_time': self.trigger_time,
            'message': self.message,
            'time_expression': self._get_time_expression()
        }

    def _extract_time_components(self):
        """Extract all potential time components from the text."""
        # Search for each pattern type
        for component_type, pattern in self.TIME_PATTERNS.items():
            matches = re.finditer(pattern, self.text, re.IGNORECASE)
            for match in matches:
                if component_type == 'interval':
                    # For intervals, capture both the quantity and unit
                    self.time_components[component_type] = {
                        'quantity': int(match.group(1)),
                        'unit': match.group(2),
                        'full_match': match.group(0)
                    }
                elif component_type == 'date':
                    # For dates, capture day, month, and optional year
                    day = match.group(1)
                    month = match.group(2)
                    year = match.group(3) if match.lastindex >= 3 else None
                    self.time_components[component_type] = {
                        'day': day,
                        'month': month,
                        'year': year,
                        'full_match': match.group(0)
                    }
                else:
                    # For other types, just store the matched value
                    self.time_components[component_type] = {
                        'value': match.group(0),
                        'full_match': match.group(0)
                    }

                    # For specific time patterns, also extract the actual time value
                    if component_type == 'specific_time' or component_type == 'time_with_at':
                        time_value = match.group(1) if component_type == 'time_with_at' else match.group(0)
                        self.time_components[component_type]['time_value'] = time_value

    def _identify_keywords(self):
        """Identify special keywords that modify how time expressions should be interpreted."""
        for keyword, pattern in self.KEYWORDS.items():
            if re.search(pattern, self.text, re.IGNORECASE):
                self.keywords[keyword] = True

    def _determine_trigger_time(self):
        """
        Determine the trigger time based on extracted components and keywords.
        This is the central logic that combines all extracted information.
        """
        now = datetime.datetime.now()

        # Case 1: Interval specified (e.g., "in 30 minutes")
        if 'interval' in self.time_components:
            interval_data = self.time_components['interval']
            quantity = interval_data['quantity']
            unit = interval_data['unit']

            # Get the seconds multiplier from our time units mapping
            seconds_multiplier = self.TIME_UNITS.get(unit.lower(), 60)  # Default to minutes if unknown
            total_seconds = quantity * seconds_multiplier

            self.trigger_time = now + datetime.timedelta(seconds=total_seconds)
            return

        # Case 2: Specific time or time with "at" (e.g., "3pm" or "at 3pm")
        time_value = None
        if 'time_with_at' in self.time_components:
            time_value = self.time_components['time_with_at']['time_value']
        elif 'specific_time' in self.time_components:
            time_value = self.time_components['specific_time']['time_value']

        date_value = None
        if 'date' in self.time_components:
            date_data = self.time_components['date']
            date_str = f"{date_data['day']} {date_data['month']}"
            if date_data['year']:
                date_str += f" {date_data['year']}"
            date_value = date_str

        day_adjustment = 0
        if 'tomorrow' in self.time_components:
            day_adjustment = 1
        elif 'next_week' in self.time_components:
            day_adjustment = 7
        elif 'next_month' in self.time_components:
            # Approximate next month as 30 days
            day_adjustment = 30

        # Combine date and time if both exist
        if time_value and date_value:
            datetime_str = f"{date_value} {time_value}"
            self.trigger_time = dateparser.parse(
                datetime_str,
                settings={
                    'PREFER_DATES_FROM': 'future',
                    'RELATIVE_BASE': now,
                    'TIMEZONE': 'local',
                    'DATE_ORDER': 'DMY'
                }
            )
            return

        # Handle just time (today or day adjustment)
        if time_value:
            # Parse the time
            parsed_time = dateparser.parse(
                time_value,
                settings={
                    'PREFER_DATES_FROM': 'future',
                    'RELATIVE_BASE': now,
                    'TIMEZONE': 'local'
                }
            )

            if parsed_time:
                # Keep the parsed time but adjust to today's date
                self.trigger_time = datetime.datetime.combine(
                    now.date(),
                    parsed_time.time()
                )

                # Apply day adjustment if any
                if day_adjustment > 0:
                    self.trigger_time += datetime.timedelta(days=day_adjustment)
                elif self.trigger_time <= now:
                    # If the time is in the past today, assume tomorrow
                    self.trigger_time += datetime.timedelta(days=1)

                return

        # Handle just date (assume default time of 9am)
        if date_value:
            parsed_date = dateparser.parse(
                date_value,
                settings={
                    'PREFER_DATES_FROM': 'future',
                    'RELATIVE_BASE': now,
                    'TIMEZONE': 'local',
                    'DATE_ORDER': 'DMY'
                }
            )

            if parsed_date:
                # Set a default time (9am) if none specified
                self.trigger_time = datetime.datetime.combine(
                    parsed_date.date(),
                    datetime.time(9, 0)  # 9:00 AM
                )
                return

        # If we get here and no components were recognized, try parsing the whole text
        self.trigger_time = dateparser.parse(
            self.text,
            settings={
                'PREFER_DATES_FROM': 'future',
                'RELATIVE_BASE': now,
                'TIMEZONE': 'local',
                'DATE_ORDER': 'DMY'
            }
        )

    def _extract_message(self):
        """
        Extract the actual reminder message by removing time expressions
        and special keywords from the original text.
        """
        message = self.original_text

        # First, identify prepositions that precede time components
        preposition_patterns = []

        # Special case for "on" preceding a date
        if 'date' in self.time_components:
            date_match = self.time_components['date']['full_match']
            on_date_pattern = r'on\s+' + re.escape(date_match)
            on_match = re.search(on_date_pattern, message, re.IGNORECASE)
            if on_match:
                preposition_patterns.append(on_match.group(0))

        # Special case for "at" preceding a time
        if 'specific_time' in self.time_components:
            time_match = self.time_components['specific_time']['full_match']
            at_time_pattern = r'at\s+' + re.escape(time_match)
            at_match = re.search(at_time_pattern, message, re.IGNORECASE)
            if at_match:
                preposition_patterns.append(at_match.group(0))

        # Remove all identified preposition patterns
        for pattern in preposition_patterns:
            message = re.sub(r'\s*' + re.escape(pattern) + r'\s*', ' ', message, flags=re.IGNORECASE)

        # Remove all time components
        for component_type, data in self.time_components.items():
            if 'full_match' in data:
                message = re.sub(r'\s*' + re.escape(data['full_match']) + r'\s*', ' ', message, flags=re.IGNORECASE)

        # Remove special keywords if they're at the beginning of the text
        for keyword in self.keywords:
            if keyword in self.keywords and self.keywords[keyword]:
                pattern = r'^\s*' + re.escape(keyword) + r'\b\s*'
                message = re.sub(pattern, '', message, flags=re.IGNORECASE)

        # Clean up the message
        message = re.sub(r'\s+', ' ', message).strip()

        # Remove dangling prepositions left at end of message (common after removing time expressions)
        message = re.sub(r'\s+(at|on|by|in|for|before)$', '', message, flags=re.IGNORECASE)

        # Remove dangling prepositions left at beginning of message
        message = re.sub(r'^(at|on|by|in|for|before)\s+', '', message, flags=re.IGNORECASE)

        # If after all removals we have an empty string, use a default message
        self.message = message if message else "Reminder"

    def _get_time_expression(self):
        """
        Reconstruct a time expression from the components for logging purposes.
        """
        if self.trigger_time:
            # Format the time expression based on what components we found
            if 'interval' in self.time_components:
                return self.time_components['interval']['full_match']
            elif 'date' in self.time_components and ('time_with_at' in self.time_components or 'specific_time' in self.time_components):
                # Date + Time
                time_part = self.time_components.get('time_with_at', {}).get('full_match') or self.time_components.get('specific_time', {}).get('full_match')
                return f"{self.time_components['date']['full_match']} {time_part}"
            elif 'date' in self.time_components:
                # Just date
                return self.time_components['date']['full_match']
            elif 'time_with_at' in self.time_components:
                # Just time with 'at'
                return self.time_components['time_with_at']['full_match']
            elif 'specific_time' in self.time_components:
                # Just specific time
                return self.time_components['specific_time']['full_match']
            else:
                # Fallback to formatted datetime
                return self.trigger_time.strftime('%Y-%m-%d %H:%M:%S')
        return None


def parse_reminder(text):
    """
    Parse reminder text to extract message and time using the ReminderParser.
    Handles natural language expressions.
    """
    parser = ReminderParser(text)
    result = parser.parse()

    if result['trigger_time'] is None:
        logger.error(f"Failed to parse time from: '{text}'")
        return None

    logger.debug(f"Parsed text: '{text}' to message: '{result['message']}' with time: {result['trigger_time'].isoformat()}")
    return result