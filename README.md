# PyX11FrameRenderer
A Python class to simplify running an X11 framebuffer and rendering frames. Works well in JupyterLab
<br>
## Example
```
xbd = X11Renderer(width = 1024, height = 768, display_num = 0)
xbd.on()
  ...         (in another shell try DISPLAY=:0 xclock)
plt.imshow(xbd.render())
  ...
xbd.off()
```
<br>

## Example (context manager)
```
import threading
import subprocess
import matplotlib.pyplot as plt

def run_xclock(timeout = 2):
  subprocess.run('DISPLAY=:0 timeout 2 xclock', shell = True)

with X11Renderer(width = 1024, height = 768, display=0) as xbd:
  t = threading.Thread(target = run_xclock, daemon=True)
  t.start()
  time.sleep(1)
  img = xbd.render()
  plt.imshow(img)
  t.join()
```

## Dependencies
This utilizes the "Xvfb", "convert", and "xdotool" shell commmands. You can install these as such (on Ubuntu)
```sudo apt update -y && sudo apt install -y xvfb imagemagick xdotool```
