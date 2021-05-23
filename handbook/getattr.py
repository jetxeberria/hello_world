class Foo(object):
    def __init__(self):
        self.attr = 0

    def __getattr__(self, attr):
        print("here")
        return self.update_attr(attr)
    
    @staticmethod
    def update_attr(attr):
        return attr + 1

foo = Foo()
print(foo.attr)
print(foo.attr)
print(foo.attr)
