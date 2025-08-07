# ascii-stream
An application for streaming ascii-videos from a local server.

Videos for the streaming can be created with my previous project: https://github.com/worian4/ascii-video.

Installation:
1. Install ```Python 3+``` on both client and server
2. Install ```C++``` and ```C++ Build Tools``` from ```VS installer``` on your client computer
3. Locate ```server.py``` and an ascii-video at your server
4. Locate ```client.py```, ```render_funcs.cpp```, ```setup.py``` at your client
5. Run ```python setup.py build_ext --inplace``` at your client to add ```render_funcs``` library to ```python```
6. Install ```vlc``` from offiial website and ```keyboard``` by running ```pip install keyboard```
7. Enter your server ip in ```client.py``` in iterable ```HOST```
8. Run ```server.py``` at your server and ```client.py``` at your client
9. Enjoy!
