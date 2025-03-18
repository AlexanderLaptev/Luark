class Index:
    def __init__(self):
        self.values = []

    def __iter__(self):
        return self.values.__iter__()

    def get_or_add(self, value):
        if value in self.values:
            return self.values.index(value)
        else:
            index = len(self.values)
            self.values.append(value)
            return index
