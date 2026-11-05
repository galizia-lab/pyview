import logging
import re

from view import VIEW


def test_custom_formatter_with_extra_entities(capsys):
    """Test custom formatting used by VIEW object"""

    _view = VIEW()
    logger = logging.getLogger("VIEW")

    # Log messages with extra entities
    extra_context = {"user_id": 123, "session_id": "abc456"}

    logger.info("This is an info message", extra=extra_context)
    logger.warning("This is a warning message", extra=extra_context)
    logger.debug("This is a debug message", extra=extra_context)

    expected_line_endings = [
        r"\[VIEW\] VIEW object initialized for offline use",
        r"\[VIEW\] Context: \{'Version': '\d+\.\d+\.dev\d+\+g[a-f0-9]+\.d\d+'\}",
        r"\[VIEW\] This is an info message",
        r"\[VIEW\] Context: \{'user_id': 123, 'session_id': 'abc456'\}",
        r"\[VIEW\] This is a warning message",
        r"\[VIEW\] Context: \{'user_id': 123, 'session_id': 'abc456'\}",
    ]

    captured = capsys.readouterr()

    captured_out_lines = captured.out.splitlines()

    for expected_line_ending, captured_line in zip(
        expected_line_endings, captured_out_lines, strict=True
    ):
        # Use regex to match the expected line ending at the end of the captured line
        pattern = expected_line_ending + r"$"
        assert re.search(pattern, captured_line), (
            f"Expected line ending '{expected_line_ending}' not found at the end of '{captured_line}'"
        )
