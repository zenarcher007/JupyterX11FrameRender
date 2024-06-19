import os
import threading
from collections import deque
import signal
import subprocess
import numpy as np
import time
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
    self.activated = False

  def setData(self, data):
    with self.lock:
      self.data = data
      self.activated = True
      self.cv.notify_all()

  def getData(self):
    while self.activated == False:
      with self.lock:
        self.cv.wait()
    self.activated = False
    return self.data

class X11Renderer:
  def __init__(self, width, height, display=0):
    self.width = width
    self.height = height
    self.display_num = display
    self._xvfb_thread = None
    self._xvfb_proc = None

  def __del__(self):
    self.off()

  # Context manager that you can use with the "with" keyword
  def __enter__(self):
    self.on()
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    self.off()
    if exc_type is not None:
      raise exc_type(exc_value).with_traceback(traceback)
  
  def _xvfb_thread_func(self, dataptr: DataWaiter):
    if self.isDisplayInUse():
      r = RuntimeError(f"Display :{self.display_num} is not available!")
      dataptr.setData(r)
      raise r
      
    try:
      cmd = ['Xvfb', f':{self.display_num}', '-screen', f'{self.display_num}', f'{self.width}x{self.height}x24']
      proc = subprocess.Popen(cmd)
      dataptr.setData(proc)
      proc.communicate()
      if proc.returncode != 0 and proc.returncode != -9:
        raise subprocess.CalledProcessError(cmd = cmd, returncode = proc.returncode)
    except Exception as e:
      dataptr.setData(e)
      raise e
    finally: # Turn "off"
      self._xvfb_thread = None
      self._xvfb_proc = None

  def isDisplayInUse(self):
    #proc = 
    #proc.stderr = open('/dev/null')
    #proc.stdout = open('/dev/null')
    try:
      subprocess.run(['xdpyinfo', '-display', f':{self.display_num}'], check = True, stdout = subprocess.DEVNULL, stderr = subprocess.DEVNULL)
      #proc.communicate()
      return True
    except subprocess.CalledProcessError as e:
      return False

  # Starts the Xvfb thread. If it is already present, does nothing.
  def on(self, wait = True):
    if self._xvfb_thread is not None:
      return
    dataptr = DataWaiter() # Retrieve the PID by sending in a datawaiter, and reading from it after starting the process
    self._xvfb_thread = threading.Thread(target = self._xvfb_thread_func, args=(dataptr,), daemon=True)
    self._xvfb_thread.start()
    while wait:
      if self.isDisplayInUse() or not self._xvfb_thread.is_alive():
        break
      else:
        time.sleep(0.2)
    data = dataptr.getData() # Should hang until there is an item present in the queue
    if isinstance(data, Exception):
      raise CalledProcessError from data
    self._xvfb_proc = data
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
      raise RuntimeError("X11 thread is not running!")
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
    
