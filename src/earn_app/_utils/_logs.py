import os
import logging

logger: logging.Logger = logging.getLogger("earn_app")
httpx_logger: logging.Logger = logging.getLogger("httpx")


def _basic_config() -> None:
    # e.g. [2023-10-05 14:12:26 - earn_app._base_client:818 - DEBUG] HTTP Request: POST http://127.0.0.1:4010/foo/bar "200 OK"
    """
    Configure the global logging format and date format for log messages.
    
    Sets the log message format to include timestamp, logger name, line number, log level, and message content.
    """
    logging.basicConfig(
        format="[%(asctime)s - %(name)s:%(lineno)d - %(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def setup_logging() -> None:
    """
    Configure application and HTTP client logging based on the EARN_APP_LOG environment variable.
    
    If EARN_APP_LOG is set to "debug" or "info", applies a standard logging format and sets both the application and httpx loggers to the corresponding level. No changes are made for other values or if the variable is unset.
    """
    env = os.environ.get("EARN_APP_LOG")
    if env == "debug":
        _basic_config()
        logger.setLevel(logging.DEBUG)
        httpx_logger.setLevel(logging.DEBUG)
    elif env == "info":
        _basic_config()
        logger.setLevel(logging.INFO)
        httpx_logger.setLevel(logging.INFO)
