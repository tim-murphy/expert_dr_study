# simple class that contains AOI information

class AOI:
    def __init__(self, name, fixation_count=0, visits=0, total_time_sec=0):
        self.name = name
        self.fixation_count = fixation_count
        self.visits = visits
        self.total_time_sec = total_time_sec

    # add fixation stats
    def addFixation(self, duration_sec, new_visit):
        if new_visit:
            self.visits += 1
        self.fixation_count += 1
        self.total_time_sec += duration_sec

    # CSV header, and also the format for the __str__ method
    @staticmethod
    def csvHeader():
        return "name,fixation_count,visits,total_time_sec"

    # CSV representation of the AOI
    def __str__(self):
        return ",".join(map(str, [self.name, self.fixation_count, self.visits,
                                  self.total_time_sec]))
        

# EOF
