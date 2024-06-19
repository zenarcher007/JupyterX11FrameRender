# JupyterX11FrameRender
A Python class to simplify running an X11 framebuffer and rendering frames in jupyterlab
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

## Dependencies
This utilizes the "Xvfb", "convert", and "xdotool" shell commmands. You can install these as such (on Ubuntu)
```sudo apt update -y && sudo apt install -y xvfb imagemagick xdotool```
