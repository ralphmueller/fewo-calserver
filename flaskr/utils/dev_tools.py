'''
Created on 13.01.2023

Timer class: code profiling

@author: ralph

    Timer class: credit https://realpython.com/python-timer/#creating-a-python-timer-class
'''
from time import perf_counter


class TimerError(Exception):
    """A custom exception used to report errors in use of Timer class"""


class Timer:
    def __init__(self, logger=print):
        self._start_time = None
        self._logger = logger

    def start(self, user_text=''):
        """Start a new timer"""
        if self._start_time is not None:
            raise TimerError("Timer is running. Use .stop() to stop it")
        self._user_text = user_text
        self._start_time = perf_counter()

    def stop(self):
        """Stop the timer, and report the elapsed time"""
        if self._start_time is None:
            raise TimerError("Timer is not running. Use .start() to start it")

        elapsed_time = perf_counter() - self._start_time
        self._start_time = None
        self._logger(f"{self._user_text} elapsed time: {elapsed_time:0.4f}")
