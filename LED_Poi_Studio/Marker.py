import os
import os.path
import sys


config_name = 'projectFile.txt'

# determine if application is a script file or frozen exe
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
elif __file__:
    application_path = os.path.dirname(__file__)

config_path = os.path.join(application_path, config_name)


backup_file = config_path


#dirname = os.path.dirname(__file__)
#backup_file = dirname + '/markers_backup.txt'

class MarkerList:
    def __init__(self):
        self.List = []
        if os.path.exists(backup_file):
            print("backup file found")
            self.f = open(backup_file, "r")
        else:
            self.f = open(backup_file, "w")
            print("no backup file found - new backup file created")
        self.reload_backup()

    def reload_backup(self):
        self.f = open(backup_file, "r")
        str_input = self.f.read()
        backup_data = []
        [backup_data.append(b.split()) for b in str_input.splitlines()]
        print(backup_data)
        self.List = backup_data
        self.f.close()

    def add_marker(self, number, time_stamp, ID, mode, picture, color, velocity, send_status):
        self.List.append([number, time_stamp, ID, mode, picture, color, velocity, send_status])
        self.update_backup_file()

    def update_backup_file(self):
        self.f = open(backup_file, "w")
        for x in self.List:
            for i in x:
                self.f.write(str(i) + " ")
            self.f.write("\n")
        self.f.close()

    def output_list_as_string(self):
        output = ""
        if len(self.List) > 0:
            for x in self.List:
                output += f"\nMarker {x[0]} - Time: {x[1]} - ID {x[2]} - Mode {x[3]} - Picture: {x[4]} - Color {x[5]} - Velocity {x[6]}- Status Sent: {x[7]}"
        return output

    def delete_last(self):
        if len(self.List) > 0:
            self.List.pop()
            self.update_backup_file()
            print("Last Marker deleted")
        else:
            print("List empty")

    def reset_send_status_all(self):
        for x in self.List:
            x[-1] = "False"

    def get_marker(self):
        return self.List

    def get_marker_time_ms_by_index(self, index):
        ms = 0
        if index < len(self.List):
            m = self.List[index]
            ms = int(m[1][11]) + int(m[1][10]) * 10 + int(m[1][9]) * 100 + int(m[1][7]) * 1000 + int(m[1][6]) * 10000 + int(m[1][4]) * 60 * 1000
            if ms < 0 or ms > 1200000:  # 20 min
                ms = 0
        return ms

    def get_marker_time_ms(self, marker):
        ms = int(marker[1][10]) * 10 + int(marker[1][9]) * 100 + int(marker[1][7]) * 1000 + int(marker[1][6]) * 10000 + int(
            marker[1][4]) * 60 * 1000
        if ms < 0 or ms > 1200000:  # 20 min
            ms = 0
        return ms

    def set_marker_sent_status(self, marker_number, status_new):
        for lm in self.List:
            if lm[0] == marker_number:
                lm[-1] = status_new
                print("Set sent status of marker " + str(marker_number) + " to " + str(status_new))

    def get_highest_marker_number(self):
        if len(self.List) > 0:
            # print("ListMarkers len: " + str(self.List[-1][0]))
            return int(self.List[-1][0])
        else:
            return 0

    def delete_next_marker_to_time_ms(self, time):
        target_index, target_time = self.find_nearest_to_time(time)
        if target_index > -1:
            self.List.pop(target_index)
            self.update_backup_file()
        return target_index

    def find_before_after_to_time(self, time_ms):
        index = 0
        before = 0
        after = 0
        if len(self.List) > 0:
            for m in self.List:
                pass

    def find_nearest_to_time(self, time_ms):
        tmp = 10 ** 9  # 10^6 s -> 16666 min
        count = 0
        target_index = -1
        target_time = -1
        if len(self.List) > 0:
            for m in self.List:
                # print("Time: " + str(time_ms) + " Time of Marker " + str(count) + " is " + str(self.get_marker_time_ms(m)) + " and time difference is: " + str(abs(time_ms - self.get_marker_time_ms(m))))
                if abs(time_ms - self.get_marker_time_ms(m)) < tmp:
                    tmp = abs(time_ms - self.get_marker_time_ms(m))
                    target_index = count
                    target_time = self.get_marker_time_ms(m)
                count += 1
        return target_index, target_time


