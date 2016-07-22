""" public logging API for test libraries
this module provides a public API for writing message ti the log file
and the console,Test libraries can use this like:
logger.info('my message')

instead of logging througth the standard output like:
print 'info* my message'

In addition to a programmatic interface being cleaner to use, this API has bneift that log message
have accurate timesamps
log levels
----------
it is possible to log messgae using levels "TRACE","DEBUG","INFO" and "WARN"

"""

from robot.output  import librarylogger

def write(msg, level,html=False):
    librarylogger.write(msg,level,html)

def trace(msg,html=False):
    librarylogger.trace(msg,html)

def debug(msg,htm=False):
    librarylogger.debug(msg,html)

def info(msg,html=False,also_console=False):
    librarylogger.info(msg,html,also_console)

def warn(msg,html=False):
    librarylogger.warn(msg,html)

def console(msg,newline=True):
    librarylogger.console(msg,newline)
