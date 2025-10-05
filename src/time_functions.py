# Helper functions

def format_time_string(time_passed):
    secs = time_passed % 60
    mins = time_passed // 60
    hours = mins // 60
    return f"{int(hours):02d}:{int(mins):02d}:{int(secs):02d}:{int((time_passed % 1) * 1000):03d}"