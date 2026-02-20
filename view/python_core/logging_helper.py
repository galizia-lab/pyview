import logging


class CustomFormatter(logging.Formatter):
    """
    Custom formatter that formats messages, adding context information passed via "extra"
    """

    def __init__(self, fmt=None, datefmt=None, program_name=None):

        super().__init__()
        self.program_name = program_name

    def format(self, record):

        basic_context = (
            "%(asctime)s " + f"[{self.program_name}]"
            if self.program_name
            else "" + "[%(levelname)-5.5s]"
        )
        original_format = basic_context + " %(message)s"

        if hasattr(record, "__dict__"):
            # see https://stackoverflow.com/questions/59176101/extract-the-extra-fields-in-logging-call-in-log-formatter
            extra_dict = {
                k: v
                for k, v in record.__dict__.items()
                if k
                not in [
                    "args",
                    "asctime",
                    "created",
                    "exc_info",
                    "exc_text",
                    "filename",
                    "funcName",
                    "levelname",
                    "levelno",
                    "lineno",
                    "message",
                    "name",
                    "module",
                    "msecs",
                    "msg",
                    "pathname",
                    "process",
                    "processName",
                    "relativeCreated",
                    "stack_info",
                    "thread",
                    "threadName",
                    "tskName",
                ]
            }
            if extra_dict:
                original_format += (
                    "\n" + basic_context + " Context: " + str(extra_dict)
                )
        return logging.Formatter(original_format).format(record)
