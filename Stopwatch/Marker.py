import os
import os.path

backup_file = 'C:\\Users\\felix\\PycharmProjects\\Controller\\Stopwatch\\markers_backup.txt'

class MarkerList:
    def __init__(self):
        self.List = []
        if os.path.isfile(backup_file):
            print("backup file found")
            self.f = open(backup_file, "r")
        else:
            self.f = open(backup_file, "w")
            print("no backup file found - new backup file created")
        self.reload_backup()

    def reload_backup(self):
        self.f = open(backup_file, "r")
        str_input = self.f.read()
        backup_details = []
        [backup_details.append(b.split()) for b in str_input.splitlines()]
        print(backup_details)
        self.List = backup_details
        self.f.close()

    def add_marker(self, number, time_stamp, ID, picture, send_status):
        self.List.append([number, time_stamp, ID, picture, send_status])
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
                output += f"\nMarker {x[0]} - Time: {x[1]} - ID {x[2]} - Picture: {x[3]} - Status Sent: {x[4]}"
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
            x[4] = "False"

    def get_marker(self):
        return self.List

    def get_marker_time_ms_by_index(self, index):
        ms = 0
        if index < len(self.List):
            m = self.List[index]
            ms = int(m[1][10]) * 10 + int(m[1][9]) * 100 + int(m[1][7]) * 1000 + int(m[1][6]) * 10000 + int(
                m[1][4]) * 60 * 1000
            if ms < 0 or ms > 1200000:  # 20 min
                ms = 0
        return ms

    def get_marker_time_ms(self, m):
        ms = int(m[1][10]) * 10 + int(m[1][9]) * 100 + int(m[1][7]) * 1000 + int(m[1][6]) * 10000 + int(
            m[1][4]) * 60 * 1000
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
        tmp = 10**9 # 10^6 s -> 16666 min
        count = 0
        target = 0
        if len(self.List) > 0:
            for m in self.List:
                print("Time: " + str(time) + " Time of Marker " + str(count) + " is " + str(self.get_marker_time_ms(m)) + " and time difference is: " + str(abs(time - self.get_marker_time_ms(m))))
                if abs(time - self.get_marker_time_ms(m)) < tmp:
                    tmp = abs(time - self.get_marker_time_ms(m))
                    target = count
                count += 1
            print(target)
            self.List.pop(target)
            self.update_backup_file()
            return target
        else:
            return -1

