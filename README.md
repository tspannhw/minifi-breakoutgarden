# minifi-breakoutgarden

Using MiniFi with the Pimoroni Breakout Garden Hat and Sensors

### Python -> TCP JSON -> MiniFi ListenTCP -> S2S HTTP NiFi Router -> S2S HTTP HDF 3.3 Cluster NiFi 1.8.0

![Architecture](breakoutgardenarchitecture.jpg)

### These run on Raspberry Pi 3B+ with latest Raspian Image


##  classify-nifi.py

You need to update and upgrade Raspian to newest
You need to install OpenCV from source and build.  
You need Python and PIP

pip install tensorflow

![Apache NiFi - MiniFi Flow ](GardenMiniFiFlow.jpg)


### Timothy Spann @PaasDev
