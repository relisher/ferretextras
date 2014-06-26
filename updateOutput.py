from EyeFeatureFinder import *
from FastRadialFeatureFinder import *
from SubpixelStarburstEyeFeatureFinder import *
from PipelinedFeatureFinder import *
from numpy import *
from scipy import *
from matplotlib import *
from CompositeEyeFeatureFinder import *
from FastRadialFeatureFinder import *
from threading import Thread


pipe_name = '/Users/Intern/Documents/pipe_eyes'
#restore_sigpipe = True
queue_length = 3




def child():
    
    pipeout = os.open(pipe_name, os.O_WRONLY)
    out_analysis = FastRadialFeatureFinder()
    image_queue = Queue.Queue()  
    worker = PipelinedWorkerProcessManager(queue_length) 
    output_queues = []
    output_queues.append(worker.output_queue)
    data = worker_loop(None,image_queue,output_queues)
    (im, guess) = data.worker_loop(None,image_queue,output_queues)
    
    out_analysis.reuse_storage = 0
    out_analysis.use_sse3 = 0
    out_analysis.filter = 'sepfir'
    
    
    while True:
        
        time.sleep(1)
       
        
        #debug code
      #  f = open('/Users/Intern/Documents/pipe_debug.txt','w')
      #  for i in len(pupil_coords):
       #    f.write(pupil_coords[i])  
        pupil_coords = out_analysis.analysis(im, guess, filter='sepfir')
        os.write(pipeout, '%d, %d \n' % (pupil_coords[0], pupil_coords[1]))
    
        #return None

        #os.getpid() 

    
if not os.path.exists(pipe_name):
    os.mkfifo(pipe_name)    


t = Thread(target=child)
t.start()
    
