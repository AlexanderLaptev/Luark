class Prototype:
    pass


class Program:
    def __init__(self, main_proto: Prototype):
        self.prototypes: list[Prototype] = [main_proto]
        self.main_proto = main_proto
