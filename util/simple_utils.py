import time

def calc_endtime(start_time=0):
    """
    Returns the run time in seconds as an integer to satisfy backend validation
    """
    end_time = time.time()
    run_duration = end_time - start_time
    return int(run_duration)