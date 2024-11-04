from unidecode import unidecode
import re
import time
from datetime import datetime
import logging

import numpy as np

def normalize(s: str) -> str:
    '''
    string stemming. for example: 'Ciáran 123!' -> 'ciaran123'
    :param s: unstemmed string
    :return: stemmed string
    '''
    stemmed_s = re.sub('[^0-9a-z]', '', unidecode(s.lower()))
    return stemmed_s


class Progress:

    def __init__(self):
        self.start = time.time()

        self.iter_times = []
        self.now = time.time()

        self.n = None
        self.n_done = None
        self.fraction_done = None
        self.progress_percentage = None
        self.eta = None
        self.eta_readable = None
        self.n_to_go = None
        self.time_to_go = None
        self.time_to_go_readable = None

        self.iter_times_array = None
        self.iter_times_min = None
        self.iter_times_max = None
        self.iter_times_mean = None
        self.iter_times_median = None
        self.iter_times_std = None

        self.iter_times_readable = None
        self.iter_times_max_readable = None
        self.iter_times_min_readable = None
        self.iter_times_mean_readable = None
        self.iter_times_median_readable = None
        self.iter_times_std_readable = None

    def _get_iter_times(self):
        self.iter_times.append(round(time.time() - self.now, 2))

    def _get_n(self, iterator):
        self.n = len(iterator)

    def _get_n_done(self, iteration, iterator):
        self.n_done = iterator.index(iteration) + 1

    def _get_fraction_done(self):
        self.fraction_done = self.n_done / self.n

    def _get_n_to_go(self):
        self.n_to_go = self.n - self.n_done

    def _get_progress_percentage(self):
        self.progress_percentage = str(round(self.fraction_done * 100, 2)) + "%"

    def _get_now(self):
        self.now = time.time()

    def _get_eta_readable(self):
        self.eta = self.start + ((self.now - self.start) / self.fraction_done)
        self.eta_readable = datetime.fromtimestamp(self.eta).strftime("%Y-%m-%d %H:%M:%S")

    def _get_time_to_go_readable(self):
        self.time_to_go = datetime.fromtimestamp(self.eta) - datetime.fromtimestamp(self.now)
        days = self.time_to_go.days
        hours, remainder = divmod(self.time_to_go.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        self.time_to_go_readable = ''
        if days > 0:
            self.time_to_go_readable += f'{days} days, '
        if hours > 0:
            self.time_to_go_readable += f'{hours} hours, '
        if minutes > 0:
            self.time_to_go_readable += f'{minutes} minutes and '

        self.time_to_go_readable += f'{seconds} seconds'

    def _get_iter_time_stats(self):
        self.iter_times_array = np.array(self.iter_times)
        self.iter_times_min = np.min(self.iter_times_array)
        self.iter_times_max = np.max(self.iter_times_array)
        self.iter_times_mean = np.mean(self.iter_times_array)
        self.iter_times_median = np.median(self.iter_times_array)
        self.iter_times_std = np.std(self.iter_times_array)

    @staticmethod
    def _make_time_readable(time_in_seconds):
        minutes = int(time_in_seconds / 60)
        seconds = int(time_in_seconds % 60)
        return f'{minutes}:{str(seconds).zfill(2)}'

    def _get_iter_time_stats_readable(self):
        self.iter_times_readable = [self._make_time_readable(time_in_sec) for time_in_sec in self.iter_times]
        self.iter_times_max_readable = self._make_time_readable(self.iter_times_max)
        self.iter_times_min_readable = self._make_time_readable(self.iter_times_min)
        self.iter_times_mean_readable = self._make_time_readable(self.iter_times_mean)
        self.iter_times_median_readable = self._make_time_readable(self.iter_times_median)
        self.iter_times_std_readable = self._make_time_readable(self.iter_times_std)

    def _get_properties(self, iteration, iterator):
        self._get_iter_times()

        self._get_n(iterator)
        self._get_n_done(iteration, iterator)
        self._get_fraction_done()
        self._get_n_to_go()
        self._get_progress_percentage()

        self._get_now()
        self._get_eta_readable()
        self._get_time_to_go_readable()

        self._get_iter_time_stats()
        self._get_iter_time_stats_readable()

    def print(self, iteration, iterator):
        self._get_properties(iteration, iterator)
        print(f'Done: {self.n_done} / {self.n} ({self.progress_percentage}), ETA: {self.eta_readable} '
              f'({self.time_to_go_readable}), '
              f'Average time per iteration: {self.iter_times_mean_readable} (MM:SS)',
              end='\r')

    def log(self, iteration, iterator):
        self._get_properties(iteration, iterator)
        logging.info(f'Time per iteration (MM:SS) - '
                     f'current: {self.iter_times_readable[-1]}, '
                     f'average: {self.iter_times_mean_readable}, '
                     f'min: {self.iter_times_min_readable}')
