import random

import tables


class KeyValue(tables.IsDescription):
    key = tables.StringCol(itemsize=22, dflt=" ", pos=0)
    value = tables.StringCol(itemsize=22, dflt=" ", pos=0)


def make_notification():
    return [
            ("foo[0]", "thing"),
            ("foo[1]", "stuff"),
            ("foo[1].child", "ring"),
            ("foo[2].child[0]", "ding"),
            ("random", random.random()),
        ]
    
# open a file in "w"rite mode
fileh = tables.open_file("storeage.h5", mode = "w")

root = fileh.root

notifications = fileh.create_group(root, "notifications")
notification = fileh.create_table(notifications, "notification", KeyValue)

row = notification.row

for i in xrange(10):
    for k, v in make_notification():
        row['key'] = k
        row['value'] = v
        row.append()

notification.flush()

fileh.close()
