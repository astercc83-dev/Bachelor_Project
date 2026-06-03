import queue


my_box = queue.Queue()

my_box.put("طوبة 1")
my_box.put("طوبة 2")
my_box.put("طوبة 3")

first_brick = my_box.get()
print(first_brick)

second_brick = my_box.get()
print(second_brick)

third_brick = my_box.get()
print(third_brick)