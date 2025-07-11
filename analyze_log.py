import re
import statistics
import glob
from datetime import datetime
import numpy as np

def analyze_log(filename):
    """
    Parses the log file, computes and prints:

    - Number of hours between the first and last initializations
    - Initialization times
        - Count
        - Mean
        - Median
        - Max
        - p99
        - p99.9
        - p99.99
    """
    timestamp_pattern = re.compile(r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})")
    init_time_pattern = re.compile(r"Initialization completed in ([0-9.]+)s")
    datetime_format = "%Y-%m-%d %H:%M:%S,%f"

    init_times = []
    first_time = None
    last_time = None

    with open(filename, "r") as f:
        for line in f:
            ts_match = timestamp_pattern.match(line)
            if ts_match:
                this_time = datetime.strptime(ts_match.group(1), datetime_format)
                if not first_time:
                    first_time = this_time
                last_time = this_time
            init_match = init_time_pattern.search(line)
            if init_match:
                init_times.append(float(init_match.group(1)))

    if first_time and last_time:
        span_seconds = (last_time - first_time).total_seconds()
        span_hours = span_seconds / 3600.0
        print(f"Timespan: {span_hours:.2f} hours (from {first_time} to {last_time})")
    else:
        print("No timestamped log lines found.")

    if init_times:
        inits_np = np.array(init_times)
        p99 = np.percentile(inits_np, 99) if len(init_times) > 1 else init_times[0]
        p99_9 = np.percentile(inits_np, 99.9) if len(init_times) > 1 else init_times[0]
        p99_99 = np.percentile(inits_np, 99.99) if len(init_times) > 1 else init_times[0]
        print(f"Inits:  {len(init_times)}")
        print(f"Mean:   {statistics.mean(init_times):.3f} s")
        print(f"Median: {statistics.median(init_times):.3f} s")
        print(f"Max:    {max(init_times):.3f} s")
        print(f"p99:    {p99:.3f} s")
        print(f"p99.9:  {p99_9:.3f} s")
        print(f"p99.99: {p99_99:.3f} s")
    else:
        print("No initialization times found in the log.")

def find_latest_logfile():
    """
    Returns the lexicographically latest logfile matching repro_*.log in the current directory.
    """
    logfiles = glob.glob("repro_*.log")
    if not logfiles:
        return None
    logfiles.sort()
    return logfiles[-1]

if __name__ == "__main__":
    latest_logfile = find_latest_logfile()
    if latest_logfile:
        print(f"Using latest log file: {latest_logfile}")
        analyze_log(latest_logfile)
    else:
        print("No matching log files found.")