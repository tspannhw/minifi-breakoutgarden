# First Pass, just run it
# Second Pass, run with nohup and &
# Third Pass, Put this into a RPI Raspian Service
cd /opt/demo
python2.7 -W ignore /opt/demo/brk.py 2>/dev/null
