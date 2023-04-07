"""
debug.py
Usage:
```
from debug import get_logger
log = get_logger("default")
```
"""

__version__ = "2023.04.07-slim"

logging_set_up = False
import os
import sys
import traceback
import logging
import logging.config
import yaml
# from flask import Response, jsonify, render_template
import functools

from colorama import just_fix_windows_console, Fore, Back, Style
just_fix_windows_console()

import logging

basedir = os.path.dirname(os.path.realpath(__file__))
global loggers
loggers = {}

logs_dir = os.path.join(basedir, 'logs')
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)


def addLoggingLevel(levelName, levelNum, methodName=None):
    """
    Comprehensively adds a new logging level to the `logging` module and the
    currently configured logging class.

    `levelName` becomes an attribute of the `logging` module with the value
    `levelNum`. `methodName` becomes a convenience method for both `logging`
    itself and the class returned by `logging.getLoggerClass()` (usually just
    `logging.Logger`). If `methodName` is not specified, `levelName.lower()` is
    used.

    To avoid accidental clobberings of existing attributes, this method will
    raise an `AttributeError` if the level name is already an attribute of the
    `logging` module or if the method name is already present 

    Example
    -------
    >>> addLoggingLevel('TRACE', logging.DEBUG - 5)
    >>> logging.getLogger(__name__).setLevel("TRACE")
    >>> logging.getLogger(__name__).trace('that worked')
    >>> logging.trace('so did this')
    >>> logging.TRACE
    5

    Mad Physicist
    https://stackoverflow.com/questions/2183233/how-to-add-a-custom-loglevel-to-pythons-logging-facility/35804945#35804945
    You can find an even more detailed implementation in the utility library I maintain, haggis. The function haggis.logs.add_logging_level is a more production-ready implementation of this answer.
    """
    if not methodName:
        methodName = levelName.lower()

    if hasattr(logging, levelName):
        raise AttributeError('{} already defined in logging module'.format(levelName))
    if hasattr(logging, methodName):
        raise AttributeError('{} already defined in logging module'.format(methodName))
    if hasattr(logging.getLoggerClass(), methodName):
        raise AttributeError('{} already defined in logger class'.format(methodName))

    # This method was inspired by the answers to Stack Overflow post
    # http://stackoverflow.com/q/2183233/2988730, especially
    # http://stackoverflow.com/a/13638084/2988730
    def logForLevel(self, message, *args, **kwargs):
        if self.isEnabledFor(levelNum):
            self._log(levelNum, message, args, **kwargs)

    def logToRoot(message, *args, **kwargs):
        logging.log(levelNum, message, *args, **kwargs)

    logging.addLevelName(levelNum, levelName)
    setattr(logging, levelName, levelNum)
    setattr(logging.getLoggerClass(), methodName, logForLevel)
    setattr(logging, methodName, logToRoot)


# region Custom logging levels
# Can be added here or no module level
addLoggingLevel("MESSAGE", logging.CRITICAL + 10)
# endregion



class ColoredFormatter(logging.Formatter):
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: Style.DIM + format + Style.RESET_ALL,
        logging.INFO: Fore.CYAN + format + Style.RESET_ALL,
        logging.WARNING: Fore.YELLOW + format + Style.RESET_ALL,
        logging.ERROR: Fore.RED + format + Style.RESET_ALL,
        logging.CRITICAL: Back.RED + Fore.WHITE + format + Style.RESET_ALL,
        logging.MESSAGE: Fore.MAGENTA + format + Style.RESET_ALL
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def setup_logging(
        default_path=os.path.join(basedir, "config", 'logger.yaml'),
        default_level=logging.INFO,
        env_key='LOG_CFG',
        logname=None
):
    """
    Setup logging configuration
    """
    caller = sys._getframe(1).f_globals.get('__name__')
    if caller != "debug":
        print("DEBUG.PY - setup_logging - WARNING - Deprecated use of debug.py by {}".format(caller))

    path = default_path
    value = os.getenv(env_key, None)
    if value:
        path = value
    if os.path.exists(path):
        with open(path, 'rt') as f:
            config = yaml.safe_load(f.read())

        for handler, data in config['handlers'].items():
            if 'filename' in data:
                logpath = os.path.join(logs_dir, config['handlers'][handler]['filename'])
                print(
                    "DEBUG.PY - setup_logging - Setting up logger '{}' requested by ({}), filepath is set to: {}; ".format(
                        handler,
                        caller,
                        logpath))
                config['handlers'][handler]['filename'] = logpath

        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=default_level)


def get_logger(name):
    caller = sys._getframe(1).f_globals.get('__name__')
    global loggers
    if loggers.get(name):
        print("DEBUG.PY - get_logger - ({}) requested logger '{}', using existing logger.".format(caller, name))
        logger = loggers.get(name)
        # coloredlogs.install(level='DEBUG', logger=logger, fmt='# %(name)s - %(levelname)-8s - %(message)s')
        return logger
    else:
        print("DEBUG.PY - get_logger - ({}) requested logger '{}', setting up new logger. ({})".format(caller, name,
                                                                                                       list(
                                                                                                           loggers.keys())))
        logger = logging.getLogger(name)
        # coloredlogs.install(level='DEBUG', logger=logger, fmt='# %(name)s - %(levelname)-8s - %(message)s')
        loggers[name] = logger
        return logger


log = get_logger("default")


def catch_errors(f):
    @functools.wraps(f)
    def wrapped(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            traceback.print_exc()
            log.error(f"Error in function {f.__name__}: {str(e)}", exc_info=True)
            return None

    return wrapped


# def catch_errors_json(f):
#     @functools.wraps(f)
#     def wrapped(*args, **kwargs):
#         try:
#             return f(*args, **kwargs)
#         except Exception as e:
#             traceback.print_exc()
#             return jsonify({"error": str(e), "traceback": traceback.format_exc()})

#     return wrapped


# def catch_errors_html(f):
#     @functools.wraps(f)
#     def wrapped(*args, **kwargs):
#         try:
#             return f(*args, **kwargs)
#         except Exception as e:
#             traceback.print_exc()
#             return render_template("error.html", error=str(e), details=traceback.format_exc())

#     return wrapped


if not logging_set_up:
    setup_logging()
