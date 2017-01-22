#!/bin/python3
import os
def stop():
    os.system("kill -2 `cat ~/.studdp/studdp.pid`")
