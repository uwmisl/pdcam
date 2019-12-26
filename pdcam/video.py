import cv2
import numpy as np
import threading
import time

from picamera import PiCamera

from pdcam.grid import find_grid_transform
from pdcam.plotting import mark_qr_code, mark_template

class AsyncGridLocate(object):
    def __init__(self, grid_reference, callback=None, timeout_frames=3):
        self.callback = callback
        self.grid_reference = grid_reference
        self.timeout_frames = timeout_frames
        self.fail_count = 0
        self.pending_image = None
        self.latest_result = (None, [])
        self.cv = threading.Condition()
        self.thread = threading.Thread(target=self.thread_entry)
        self.thread.daemon = True
        self.thread.start()

    def push(self, image):
        """Push a new image to be processed
        
        Images aren't queued. If you push a new image before processing has 
        begun on the previous image, the previous image will be dropped. 
        """
        with self.cv:
            self.pending_image = image
            self.cv.notify()

    def latest(self):
        with self.cv:
            transform, qrinfo = self.latest_result

        return transform, qrinfo

    def thread_entry(self):
        while True:
            with self.cv:
                self.cv.wait_for(lambda: self.pending_image is not None)
                img = self.pending_image
                self.pending_image = None

            # Now we've got the image, and cleared pending image, 
            # we can release the lock and do the processing
            transform, qrinfo = find_grid_transform(self.grid_reference, img)
            
            with self.cv:
                if transform is not None:
                    self.fail_count = 0
                    self.latest_result = (transform, qrinfo)
                else:
                    self.fail_count += 1
                    if self.fail_count > self.timeout_frames:
                        self.latest_result = (transform, qrinfo)

            if self.callback is not None:
                self.callback(transform, qrinfo)
    

class Video(object):
    """Video capture process

    Launches background threads to continuously capture frames from raspberry PI 
    camera (MMAL API) and process them to locate QR codes.
    """

    WIDTH = 1024
    HEIGHT = 768
    NBUFFER = 3
    PROCESS_PERIOD = 1.0
    def __init__(self, grid_reference, grid_layout):
        self.frame_number = 0
        self.grid_layout = grid_layout
        self.frames = [np.empty((self.WIDTH * self.HEIGHT * 3,), dtype=np.uint8) for _ in range(self.NBUFFER)]
        self.frame_locks = [threading.Lock() for _ in range(self.NBUFFER)]
        self.lock = threading.Lock()
        self.frame_cv = threading.Condition(self.lock)
        self.active_buffer = 0
        self.last_process_time = 0.0

        if grid_reference is not None:
            self.grid_finder = AsyncGridLocate(grid_reference)
        else:
            self.grid_finder = None
        self.capture_thread = threading.Thread(target=self.capture_thread_entry)
        self.capture_thread.daemon = True
        self.capture_thread.start()
    
    def capture_thread_entry(self):
        print("Running capture thread")
        with PiCamera() as camera:
            camera.resolution = (self.WIDTH, self.HEIGHT)
            camera.framerate = 30
            camera.start_preview()

            while True:
                next_buffer = (self.active_buffer + 1) % self.NBUFFER
                with self.frame_locks[next_buffer]:
                    camera.capture(self.frames[next_buffer], 'bgr', use_video_port=True)
                    self.frames[next_buffer] = self.frames[next_buffer].reshape((self.HEIGHT, self.WIDTH, 3))
                    cur_time = time.monotonic()
                    if cur_time - self.last_process_time > self.PROCESS_PERIOD:
                        self.last_process_time = cur_time
                        self.grid_finder.push(self.frames[next_buffer].copy())
                with self.lock:
                    self.active_buffer = next_buffer
                    self.frame_number += 1
                    self.frame_cv.notify_all()

    def latest_transform(self):
        """Get the latest transform solution

        Transform is a 3x3 numpy array representing a homography.
        It may be None, if no transform is found.
        """
        transform, _ = self.grid_finder.latest()
        return transform

    def markup(self, image):
        # Make a copy so we don't modify the original np array
        image = image.copy()
        transform, qrinfo = self.grid_finder.latest()
        for qr in qrinfo:
            mark_qr_code(image, qr.polygon)
        
        if transform is not None:
            mark_template(image, self.grid_layout, transform)
        
        return image
            
    def latest_jpeg(self, min_frame_num=0, markup=False):
        """Get the latest capture as a JPEG

        min_frame_num can be used for sequential calls to prevent receiving the
        same frame twice.
        """
        if min_frame_num is None:
            min_frame_num = 0
        # Hold the global lock just long enough to read self.active_buffer and get the frame lock
        self.frame_cv.acquire()
        self.frame_cv.wait_for(lambda: self.frame_number >= min_frame_num)
        frame_num = self.frame_number
        with self.frame_locks[self.active_buffer]:
            self.frame_cv.release()
            if markup:
                image = self.markup(self.frames[self.active_buffer])
            else:
                image = self.frames[self.active_buffer]
            (flag, encoded_image) = cv2.imencode(".jpg", image)
            if not flag: 
                print("Error encoding jpeg")

        return bytearray(encoded_image), frame_num

    def mjpeg_frame_generator(self, markup=False):
        """Return a generator which will yield JPEG encoded frames as they become available
        Bytes are preceded by a `--frame` separator, and a content header,
        is included so it can be returned as part of a HTTP multi-part response. 
        """
        last_fn = 0
        while True:
            data = None
            with self.frame_cv:
                if self.frame_number > last_fn:
                    last_fn = self.frame_number
                    if markup:
                        image = self.markup(self.frames[self.active_buffer])
                    else:
                        image = self.frames[self.active_buffer]
                    # encode the frame in JPEG format
                    (flag, encoded_image) = cv2.imencode(".jpg", image)

                    if not flag: 
                        print("Error encoding image %d" % self.frame_number)
                        continue

                    data = b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encoded_image) + b'\r\n'
                else:
                    self.frame_cv.wait()
            if data is not None:
                yield data