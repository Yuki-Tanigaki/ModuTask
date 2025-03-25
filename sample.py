import copy

class A:

    def __init__(self, name, list):
        self.name = name
        self.list = list

original_list = [A("A", [0, 0]), A("A2", [0, 0]), A("A3", [0, 0])]

copy1 = list(original_list)
copy2 = list(original_list)

copy1[1].list = [1, 0]
copy1.pop(0)

print(copy1[0].name)
print(copy2[0].name)
print(copy1[0].list)
print(copy2[0].list)

print(copy1[1].name)
print(copy2[1].name)
print(copy1[1].list)
print(copy2[1].list)


