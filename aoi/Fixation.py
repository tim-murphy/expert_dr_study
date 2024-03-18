# simple class that contains information about a fixation

class Fixation:
    def __init__(self, fixation_id, start_time_sec, duration_sec,
                 x_pos_px, y_pos_px, aoi):
        self.fixation_id = fixation_id
        self.start_time_sec = start_time_sec
        self.duration_sec = duration_sec
        self.pos_px = (x_pos_px, y_pos_px)
        self.aoi = aoi

    # CSV header, which is also the data order for __str__
    @staticmethod
    def csvHeader():
        return "fixation_id,start_time_sec,duration_sec,x_pos_px,y_pos_px,aoi"

    # the fixation in a CSV format
    def __str__(self):
        return ",".join(map(str, [self.fixation_id, self.start_time_sec,
                                  self.duration_sec, *self.pos_px, self.aoi]))

# EOF
