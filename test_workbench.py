class A():

    def __init__(self):
        print(self.ATTR)


class B(A):
    ATTR = "WORLD"
    def __init__(self):
        super().__init__()


B()