import os
import threading
from collections import deque
import signal
import subprocess
import numpy as np
os.environ['MUJOCO_GL'] = 'egl' # Tells mujoco to use an Nvidia GPU for display buffer rendering. Remove this if this does not apply to you
# To install dependencies and other useful tools on Ubuntu, open a terminal and type:
# sudo apt update -y && sudo apt install -y xvfb xterm x11-apps imagemagick xdotool

# Consists of a condition variable and some data. A thread can pass data this way, kind of like a pointer
# getData() blocks until some data has been set by setData()
class DataWaiter:
  def __init__(self):
    self.data = None
    self.lock = threading.Lock()
    self.cv = threading.Condition(self.lock)

  def setData(self, data):
    with self.lock:
      self.data = data
      self.cv.notify_all()

  def getData(self):
    while self.data is None:
      with self.lock:
        self.cv.wait()
    return self.data

# Example:
# xbd = X11Renderer(width = 1024, height = 768, display_num = 0)
# xbd.on()
# ...
# plt.imshow(xbd.render())
# ...
# xbd.off()
class X11Renderer:
  def __init__(self, width, height, display_num=0):
    self.width = width
    self.height = height
    self.display_num = display_num
    self._xvfb_thread = None
    self._xvfb_proc = None

  def __del__(self):
    self.off()
  
  def _xvfb_thread_func(self, dataptr: DataWaiter):
    proc = subprocess.Popen(['Xvfb', f':{self.display_num}', '-screen', f'{self.display_num}', f'{self.width}x{self.height}x24'])
    dataptr.setData(proc)
    proc.communicate()

  # Starts the Xvfb thread. If it is already present, does nothing.
  def on(self):
    if self._xvfb_thread is not None:
      return
    dataptr = DataWaiter() # Retrieve the PID by sending in a deque, and reading from it after starting the process
    self._xvfb_thread = threading.Thread(target = self._xvfb_thread_func, args=(dataptr,), daemon=True)
    self._xvfb_thread.start()
    self._xvfb_proc = dataptr.getData() # Should hang until there is an item present in the queue
    assert(self._xvfb_proc is not None and self._xvfb_thread is not None)
  
  # Stops the Xvfb thread. If it is not present, does nothing.
  def off(self):
    if self._xvfb_thread is None or self._xvfb_proc is None:
      return
    self._xvfb_proc.kill()
    self._xvfb_thread.join()
    self._xvfb_thread = None
    self._xvfb_proc = None
  
  # Captures and returns the current X11 frame as a numpy array (viewable from plt.show())
  def render(self):
    if self._xvfb_thread is None:
      raise RuntimeError("Backdrop thread is not running!")
    out = None
    with subprocess.Popen(['sh', '-c', f'DISPLAY=:{self.display_num} xwd -root -silent | convert xwd:- -depth 8 rgb:-'], stdout=subprocess.PIPE) as proc:
      out = proc.stdout.read()
    dt = np.dtype('uint8')
    dt = dt.newbyteorder('>')
    arr = np.frombuffer(out, dtype = dt)
    arr = arr.reshape(self.height, self.width, 3)
    return arr

  # Performs a mouse click at the given coordinates
  def click(self, x, y):
    subprocess.run(f'DISPLAY=:{self.display_num} xdotool mousemove {x} {y} click 1 sleep 0.01 mousemove restore', shell = True)
    
