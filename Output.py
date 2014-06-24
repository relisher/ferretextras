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

pipe_name = '/Users/Intern/Documents/pipe_eye.txt'
#restore_sigpipe = True
queue_length = 3

class Output(FastRadialFeatureFinder):
    def analysis(self, image, guess=None, **kwargs):
        
        
        # print "fr"
        im_array = image
        # im_array = image.astype(double)
        im_array = im_array[::self.ds_factor, ::self.ds_factor]

        if guess != None:
            features = guess
        else:
            features = {'pupil_size': None, 'cr_size': None}

        if self.parameters_updated or self.backend.cached_shape \
            != im_array.shape:
            logging.debug('Recaching...')
            logging.debug('Target kPixels: %s' % self.target_kpixels)
            logging.debug('Max Radius Fraction: %s' % self.max_radius_fraction)
            logging.debug('Radius steps: %s' % self.radius_steps)
            im_pixels = image.shape[0] * image.shape[1]
            self.ds_factor = int(sqrt(im_pixels / int(self.target_kpixels
                                * 1000)))
            if self.ds_factor <= 0:
                self.ds_factor = 1
            im_array = image[::self.ds_factor, ::self.ds_factor]

            self.backend.autotune(im_array)
            self.parameters_updated = 0

            self.radiuses_to_try = linspace(ceil(self.min_radius_fraction
                    * im_array.shape[0]), ceil(self.max_radius_fraction
                    * im_array.shape[0]), self.radius_steps)
            self.radiuses_to_try = unique(self.radiuses_to_try.astype(int))
            logging.debug('Radiuses to try: %s' % self.radiuses_to_try)
            logging.debug('Downsampling factor: %s' % self.ds_factor)

        ds = self.ds_factor

        S = self.backend.fast_radial_transform(im_array, self.radiuses_to_try,
                    self.alpha)
    
        S[:, 0:self.restrict_left] = -1.
        S[:, self.restrict_right:] = -1.
        S[0:self.restrict_top, :] = -1.
        S[self.restrict_bottom:, :] = -1.

        if self.albino_mode:
            (pupil_coords, cr_coords) = self.find_albino_features(S, im_array)
        else:
            (pupil_coords, cr_coords) = self.backend.find_minmax(S)

        if pupil_coords == None:
            pupil_coords = array([0., 0.])

        if cr_coords == None:
            cr_coords = array([0., 0.])

        if self.correct_downsampling:
            features['pupil_position'] = array([pupil_coords[0],
                    pupil_coords[1]]) * ds
            features['cr_position'] = array([cr_coords[0], cr_coords[1]]) * ds
            features['dwnsmp_factor_coord'] = 1
        else:
            features['pupil_position'] = array([pupil_coords[0],
                    pupil_coords[1]])
            features['cr_position'] = array([cr_coords[0], cr_coords[1]])
            features['dwnsmp_factor_coord'] = ds

        features['transform'] = S
        features['im_array'] = im_array
        features['im_shape'] = im_array.shape

        features['restrict_top'] = self.restrict_top
        features['restrict_bottom'] = self.restrict_bottom
        features['restrict_left'] = self.restrict_left
        features['restrict_right'] = self.restrict_right

        if self.return_sobel:
            # this is very inefficient, and only for debugging
            (m, x, y) = self.backend.sobel3x3(im_array)
            features['sobel'] = m

        self.result = features
        
        return pupil_coords



class ImageInformation(PipelinedWorker):
    
    
    def worker_loop(self, ff, image_queue, output_queue, id=-1):
        while(1):
            input = image_queue.get()
    
            if input is not None:
                (im, guess) = input
            else:
                im = None
                guess = None
    
            # else an image
            ff.analyze_image(im, guess)
            features = ff.get_result()
    
            # take these out because they are a bit big
            features["transform"] = None
            features["im_array"] = None
    
            # pickle the structure manually, because Queue doesn't seem to do the
            # job correctly
            output_queue.put(pickle.dumps(features))
            
            return (im, guess)

    def child():
        
        pipeout = os.open(pipe_name, os.O_WRONLY)
        out_analysis = Output()
        image_queue = Queue.Queue()  
        worker = PipelinedWorkerProcessManager(queue_length) 
        output_queues = []
        output_queues.append(worker.output_queue)
        data = ImageInformation(None,image_queue,output_queues)
        
        
        while True:
            
            time.sleep(1)
            (im, guess) = data.worker_loop(None,image_queue,output_queues)
            pupil_coords = out_analysis.analysis(im, guess)
            os.write(pipeout, '%d , %d \n' % (pupil_coords[0], pupil_coords[1]))
            
            #return None
        
            #os.getpid() 
        
    
        if not os.path.exists(pipe_name):
            os.mkfifo(pipe_name)
        
        
    t = Thread(target=child)
    t.start()
    
