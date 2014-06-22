import os, time, sys
from threading import Thread
pipe_name = '/Users/stevenrelin/Documents/pipe_eye.txt'

def child( ):
    pipeout = os.open(pipe_name, os.O_WRONLY)
    counter = 0
    while True:
        time.sleep(1)
        os.write(pipeout, 'Number %03d\n' % counter)
        counter = (counter+1) % 5
        
if not os.path.exists(pipe_name):
    os.mkfifo(pipe_name)  
    
t = Thread(target=child)
t.start()
