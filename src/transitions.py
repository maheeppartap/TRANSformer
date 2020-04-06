class Transition:
    vidstats = None

    def __init__(self, start: int, end: int, r=255, g=128, b=70):
        # which frame the transition starts and ends on
        self.start = start
        self.end = end
        self.r = r
        self.g = g
        self.b = b

    # for sorting
    def __cmp__(self, other):
        if other is Transition:
            return self.start - other.start
        else:
            return 0

    def set_rgb(self, r: int, g: int, b: int):
        self.r = r
        self.g = g
        self.b = b

    # draws something onto the frame to make the transition more prominent
    def draw_on_frame(self, frame, frame_ind):
        if Transition.vidstats is None:
            print("IMPORTANT! set vidstats before enhancing video")


class ColWipe(Transition):
    def __init__(self, start: int, end: int, scol: int, ecol: int, r=255, g=128, b=70):
        super().__init__(start, end, r, g, b)
        self.scol = scol
        self.ecol = ecol

    def draw_on_frame(self, frame, frame_ind):
        super().draw_on_frame(frame, frame_ind)


class HorWipe(Transition):
    def __init__(self, start: int, end: int, srow: int, erow: int, r=255, g=128, b=70):
        super().__init__(start, end, r, g, b)
        self.srow = srow
        self.erow = erow


class Cut(Transition):
    def __init__(self, start: int, end: int, fps=30, r=255, g=128, b=70):
        # make cut 1 second wide so we can enhance it more
        super().__init__(int(max(start-fps/2, 0)), int(end + fps/2), r, g, b)