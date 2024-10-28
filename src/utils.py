from unidecode import unidecode
import re
import time
from datetime import datetime

def stem(s: str) -> str:
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

    def show(self, iteration, iterator):
        n = len(iterator)
        counter = iterator.index(iteration) + 1
        fraction_done = counter / n

        progress_percentage = str(round(fraction_done * 100, 2)) + "%"
        now = time.time()
        eta = self.start + ((now - self.start) / fraction_done)
        time_completed = datetime.fromtimestamp(eta).strftime("%Y-%m-%d %H:%M:%S")
        delta = datetime.fromtimestamp(eta) - datetime.fromtimestamp(now)
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        time_to_go = ''
        if days > 0:
            time_to_go += f'{days} days, '
        if hours > 0:
            time_to_go += f'{hours} hours, '
        if minutes > 0:
            time_to_go += f'{minutes} minutes and '

        time_to_go += f'{seconds} seconds'

        average_compute_time = (now - self.start) / counter
        avg_minutes = int(average_compute_time / 60)
        avg_seconds = int(average_compute_time % 60)
        print(f'Done: {counter} / {n} ({progress_percentage}), ETA: {time_completed} ({time_to_go}), '
              f'Average time per loop: {avg_minutes} minutes and {avg_seconds} seconds',
              end='\r')