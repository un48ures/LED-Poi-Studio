import statistics

jitter_values = []

def calc_jitter_info(current_jitter):
    if abs(current_jitter) > 100:
        current_jitter = 1
    jitter_values.append(abs(current_jitter))
    average = statistics.mean(jitter_values)
    maximum = max(jitter_values)
    return average, maximum

def delete_jitter_values():
    jitter_values.clear()
    calc_jitter_info(0)
