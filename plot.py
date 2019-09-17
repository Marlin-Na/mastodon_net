
import os
import matplotlib as mp
import matplotlib.pyplot as plt
from datetime import datetime

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crawlerjob.log")

def read_data():
    log_file = open(LOG_FILE, "r")
    for line in log_file:
        success_count, queue_count, failed_count, time = line.rstrip().split()
        success_count = int(success_count)
        queue_count   = int(queue_count)
        failed_count  = int(failed_count)
        time          = datetime.fromtimestamp(float(time))
        yield (success_count, queue_count, failed_count, time)

if __name__ == "__main__":
    success_count, queue_count, failed_count, time = list(zip(*read_data()))
    plt.plot(time, success_count, color = "green", label="Success count")
    plt.plot(time, queue_count,   color = "yellow", label="Queue count")
    plt.legend()
    plt.show()
