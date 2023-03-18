# Pumped storage proof of concept
Pumped hydroelectric storage is a sort of a battery that uses gravity and solar energy to generate and conserve energy.
See more on [wikipedia](https://en.wikipedia.org/wiki/Pumped-storage_hydroelectricity) for more info

This project meant to create a little prototype, so to give some insight on the development quirks on building something similar on a larger scale.

I uploaded all controlling and management software, control statemachine, schematics and some fluid mechanics calculations, but the details of the actual building of the storage structure is not covered here in details.

# Setup for the desktop client
This setup assumes that VS code and docker are installed.
To view and edit the control flow and schematics diagrams. I use [diagrams.net](https://www.diagrams.net/)

VS Code steps:
 - Run ```docker-compose up -d --force-recreate statistics-db``` to start timescale db and grafana for data logging
 - You can access the grafana ui in the browser using ```localhost:3000```
 - Install extensions Docker (Microsoft), Remote-containers (Microsoft)
 - Click in the green area in the bottom left corner (Open a Remote Window)
 - Reopen in container (Select from Dockerfile)
 - Run ```xhost local:docker``` in the host command line (this will allow the GUI forwarding from the container)
 - If all goes well, you just need press F5 and it should start build and then the application with Debug.

## Quick overview
The system consists of a couple of components.
- Desktop client to allow manual testing of relays and the pump/release flow
- Arduino firmware to do the control loop
- Test rig consisting 2x 5 liters tank relays, sensors, generator, pump, solar control
- Grafana webserver to show the data

There were quite a few obsitcales during development, so I ended up not finishing the system entirely. Basically the system at this scale is not feasable, but it wasn'nt the point either
Some remarks:
- The setup is missing the voltage sensor feedback
- The whole system will not be efficient at all. The pumps take way too much current and deplete the buffer battery quickly (I needed two, to reach 2 meter pump heighs, so at least the generator gets the minimum flow to actually produce the minimum voltage)
- The 12V converter for the pumps gets super hot
- The control loop code for auto control was not really tested and most likely incomplete, so use it with caution
- The solar panel is just simply not generating enough charge to recharge the system or power the pumps
- I struggeld a lot with calibrating the tank weights to measure the level of the water. Using force sensors are cheap, but not reliable in the sense, that if the tank is moved or the rig is not horizontal, the weight and so the level will not be accurate (note: in my setup the tank has for legs and the sensor is attached to one of them)
- The tanks need to be huge in order to gain enough energy buffer. This concept makes only sense if there is a sizeable lake available.
- I did not do all the calculations on how big the pumps, tanks, generators should be, their were pretty adhoc and constrained by the available space in my apartament and of course budget (approx 5-600USD).

## Some images of the setup
Tanks
![top](https://github.com/artofimagination/pumped-storage/blob/master/docs/top_tank.jpg)
![bottom](https://github.com/artofimagination/pumped-storage/blob/master/docs/bottom_tank.jpg)

Electronics
![el1](https://github.com/artofimagination/pumped-storage/blob/master/docs/solar_electronics_box.jpg)
![el2](https://github.com/artofimagination/pumped-storage/blob/master/docs/electronics_top.jpg)
![el3](https://github.com/artofimagination/pumped-storage/blob/master/docs/electronics_bottom.jpg)

Control flow
![cf](https://github.com/artofimagination/pumped-storage/blob/master/docs/ControlFlow-AutoControl.png)
![cf](https://github.com/artofimagination/pumped-storage/blob/master/docs/ControlFlow-ManualControl.png)

Schematics
![schem](https://github.com/artofimagination/pumped-storage/blob/master/docs/Schematics.png)