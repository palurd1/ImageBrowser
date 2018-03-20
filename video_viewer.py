#!/usr/bin/pỳthon
# file encoding is utf8

import os
import sys
import subprocess
import glob

info="""
video_viewer.py by palurd1. https://github.com/palurd1/ImageBrowser
Distributed under GPLv3.

Python script that takes a video file as input, creates a folder called
'[videofile]_frames' and stores there all frames as images.  The script also
generates a viewer file called VIEWER_[videoname].html with a built-in
JavaScript to browse through the images.

This script runs on python3.6 and uses ffmpeg and ffprobe to process the
video file. The HTML viewer should be compatible with most browsers.
"""


################################################################################
# sanity check
if len(sys.argv) != 2:
    print("Error. Usage: python {} videoname".format(sys.argv[0]))
    print(info)
    quit()
input_file_name = sys.argv[1]
################################################################################


################################################################################
# SCRIPT PARAMETERS
# parameter to control the image quality, 2 to 31 (lower is better)
IMAGE_QUALITY = 2
FRAMES_DIR = input_file_name + '_frames'
OUTPUT_BASENAME = os.path.join(FRAMES_DIR, os.path.basename(input_file_name))
HTML_FILE_NAME = 'VIEWER_' + os.path.basename(input_file_name) + '.html'
################################################################################


################################################################################
# https://stackoverflow.com/questions/1806278/convert-fraction-to-float
def convert_to_float(frac_str):
    try:
        return float(frac_str)
    except ValueError:
        try:
            num, denom = frac_str.split('/')
        except ValueError:
            return None
        try:
            leading, num = num.split(' ')
        except ValueError:
            return float(num) / float(denom)
        if float(leading) < 0:
            sign_mult = -1
        else:
            sign_mult = 1
        return float(leading) + sign_mult * (float(num) / float(denom))
################################################################################


if not os.path.isdir(FRAMES_DIR):
    os.makedirs(FRAMES_DIR)

# get the video size
command = [
        'ffprobe',
        '-v', 'error',
        '-of', 'flat=s=_',
        '-select_streams', 'v:0',
        '-show_entries',
        'stream=height,width,',
        input_file_name
        ]
print(" ".join(command))
p = subprocess.run(command, stdout=subprocess.PIPE)
videoWidth  = p.stdout.decode('utf-8').split('\n')[0].split('=')[1]
videoHeight = p.stdout.decode('utf-8').split('\n')[1].split('=')[1]

# get the video fps
command = [
        'ffprobe',
        '-v', '0',
        '-of', 'csv=p=0',
        '-select_streams', '0',
        '-show_entries',
        'stream=r_frame_rate',
        input_file_name
        ]
print(" ".join(command))
p = subprocess.run(command, stdout=subprocess.PIPE)
videoFPS = convert_to_float(p.stdout.decode('utf-8')[:-1])

# generate the frames
command = [
        'ffmpeg',
        '-i',  input_file_name,
        '-qscale:v', str(IMAGE_QUALITY),
        '{}_%d.jpg'.format(OUTPUT_BASENAME)]

print(" ".join(command))
subprocess.run(command)

# get all files created
frames = sorted(glob.glob(OUTPUT_BASENAME + '*.jpg'))
print(frames[0])

with open(HTML_FILE_NAME, 'w') as html_file:
    html_file.write("""<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN"
"http://www.w3.org/TR/html4/loose.dtd">
<html>
    <head> 
        <meta http-equiv="Content-Type" content="text/html;charset=utf-8" >

        <title>
            {file_name}
        </title> 

        <script charset="utf-8">
            var FRAME_START = 1;
            var FRAME_END = {last_frame};
            var imageNumber = FRAME_START;
            var autoPlay = 0;
            var f_FPS = {videoFPS};
            var onScrollBar = 0;
            var clicked = 0

            function refresh(){{
                    document.getElementById("onlyImage").src="{OUTPUT_BASENAME}_"+imageNumber+".jpg";
                    document.getElementById("barra").value = imageNumber;
                    document.getElementById("currentFrame").textContent = imageNumber;
            }}

            function unclick(){{
                clicked = 0;
                return;
            }}

            function moveMouse(event){{
                if (clicked == 1){{
                    var x = event.pageX - document.getElementById('barra').offsetLeft; // or e.offsetX (less support, though)
                    var clickedValue = x * document.getElementById('barra').max / document.getElementById('barra').offsetWidth;
                    userInput = Math.round(clickedValue);
                    if (userInput < FRAME_START)
                        userInput = FRAME_START;
                    if (userInput > FRAME_END)
                        userInput = FRAME_END;
                    imageNumber = userInput;
                    refresh();
                }}
                return;
            }}

            function inicialitza(){{
                document.onkeydown = tecla;
                document.onmouseup = unclick;

                document.onmousemove = moveMouse;

                document.getElementById('barra').addEventListener('mouseout', function (e) {{
                    onScrollBar = 0;
                }});
                document.getElementById('barra').addEventListener('mouseover', function (e) {{
                    onScrollBar = 1;
                }});
                document.getElementById('barra').addEventListener('mousedown', function (e) {{
                    if (onScrollBar == 1){{
                        clicked = 1;
                        moveMouse(e);
                    }}
                }});
                return;
            }}

            function playForward(){{
                if (imageNumber != FRAME_END)
                {{
                    imageNumber++;
                    refresh();
                }}
                else
                    autoPlay = 0;


                if (autoPlay == 1)
                {{
                    var prova = setTimeout(playForward, 1.0/f_FPS * 1000.0);
                }}
                
                return;
            }}

            function playBackwards(){{
                if (imageNumber != FRAME_START)
                {{
                    imageNumber--;
                    refresh();
                }}
                else
                    autoPlay = 0;

                if (autoPlay == 1)
                    prova = setTimeout(playBackwards, 1.0/f_FPS * 1000);

                return;
            }}

            function tecla(event){{
                var key;
                if (!event)
                    var event = window.event;

                // For different browser compatiblity
                if (window.event)
                    key = window.event.keyCode;
                else if (event.which)
                    key = event.which;
                else
                    return;

                // ignore event if key value is zero
                // as for alt on Opera and Konqueror
                if (!key)
                    return;

                // list of keys and actions
                switch(key){{
                    // right arrow, enter, l
                    case 76:
                    case 39:
                    case 13:
                        event.preventDefault();
                        playForward();
                        break;

                    // left arrow, h
                    case 72:
                    case 37:
                        event.preventDefault();
                        playBackwards();
                        break;

                    // p
                    case 80:
                        event.preventDefault();
                        userInput = prompt("Specify play speed in FPS (current " + f_FPS + " fps):")
                        if (userInput > 0 && userInput < 100)
                            f_FPS = userInput;
                        break;

                    // b
                    case 66:
                        event.preventDefault();
                        if (autoPlay == 1)
                            autoPlay = 0;
                        else
                        {{
                            autoPlay = 1;
                            playBackwards();
                        }}
                        break;

                    // space
                    case 32:
                        event.preventDefault();
                        if (autoPlay == 1)
                            autoPlay = 0;
                        else
                        {{
                            autoPlay = 1;
                            playForward();
                        }}
                        break;

                    // g
                    case 71:
                        event.preventDefault();
                        userInput = prompt("Go to frame number (current " + imageNumber + ". min " + FRAME_START + ", max " + FRAME_END);
                        if (userInput >= FRAME_START && userInput <= FRAME_END)
                        {{
                            imageNumber = userInput;
                            refresh();
                        }}
                        break;

                    // m
                    case 77:
                        event.preventDefault();
                        // inspired by 
                        // https://stackoverflow.com/questions/8158012/how-to-scale-an-image-to-full-screen-using-javascript
                        var picture = document.getElementById("onlyImage");
                        var barra = document.getElementById('barra');

                        if (picture.style.position == 'absolute')
                        {{
                            picture.width  = document.getElementById("originalWidth").innerHTML;
                            picture.height = document.getElementById("originalHeight").innerHTML;
                            picture.style.position = 'static';

                            barra.style.position = 'static';
                        }}
                        else
                        {{

                            var imageWidth = picture.width,
                                imageHeight = picture.height,
                                maxWidth = window.innerWidth,
                                maxHeight = window.innerHeight,
                                widthRatio = maxWidth / imageWidth,
                                heightRatio = maxHeight / imageHeight;

                            var ratio = widthRatio; //default to the width ratio until proven wrong

                            if (widthRatio * imageHeight > maxHeight) {{
                                ratio = heightRatio;
                            }}

                            //now resize the image relative to the ratio
                            picture.width  = imageWidth  * ratio;
                            picture.height = imageHeight * ratio;

                            //and center the image vertically and horizontally
                            picture.style.margin = 'auto';
                            picture.style.position = 'absolute';
                            picture.style.top = 0;
                            picture.style.bottom = 0;
                            picture.style.left = 0;
                            picture.style.right = 0;
                            picture.style.zIndex = 1;

                            // set the scrollbar at the bottom and visible
                            barra.style.zIndex = 2;
                            barra.style.position = 'absolute';
                            barra.style.margin = 'auto';
                            barra.style.top = 0;
                            barra.style.left = 0;
                        }}
                        break;
                }}
                return;
            }}

            window.onload = inicialitza;
        </script> 

    <body>
        <ul>
            <li>
                ImageBrowser by palurd1. <a href="https://github.com/palurd1/ImageBrowser">https://github.com/palurd1/ImageBrowser</a>
            </li>
            <li>
                File Information
                <ul>
                    <li>
                        video name: {file_name}
                    </li>
                    <li>
                        original size: <span id="originalWidth">{videoWidth}</span>x<span id="originalHeight">{videoHeight}</span>
                    </li>
                    <li>
                        number of frames: {last_frame}
                    </li>
                    <li>
                        frame rate: {videoFPS} fps
                    </li>
                </ul>
            </li>
            <li>
                Key bindings
                <ul>
                    <li>
                        '→' (right arrow), '↲' (enter), 'l' -- next frame
                    </li>
                    <li>
                        '←' (left arrow), 'h' -- previous frame
                    </li>
                    <li>
                        'p' -- specify play speed (FPS, probably limited by rendering time)
                    </li>
                    <li>
                        'b' -- play the video backwards, at the specified FPS
                    </li>
                    <li>
                        ' ' (space) -- play the video forward, at the specified FPS
                    </li>
                    <li>
                        'g' -- go to a specific frame
                    </li>
                    <li>
                        'm' -- resize image to full window or back to its original size
                    </li>
                </ul>
            </li>
            <li>
                Tips
                <ul>
                    <li>
                        Zoom in (Ctl-wheel or Ctl+/Ctl-) to see a detail of the video.
                    </li>
                    <li>
                        Use fullscreen mode (F11) and then resize to full window with 'm'.
                    </li>
                </ul>
            </li>
        </ul>

        <center>
            Current frame: <span id="currentFrame">1</span>
            <br>
            <progress value="1" max="{last_frame}" style="width:80%" id="barra">
            </progress>
            <br>
            <img  src="{firstFrame}" id="onlyImage">
        </center>
    </body>
</html> """.format(file_name=input_file_name, last_frame=len(frames), videoFPS=videoFPS, videoWidth=videoWidth, videoHeight=videoHeight, OUTPUT_BASENAME=OUTPUT_BASENAME, firstFrame=frames[0]))
