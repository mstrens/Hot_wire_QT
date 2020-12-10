# Hot_wire

This application runs on a PC and allows to control a CNC 4 axis hot wire in order to cut e.g. wings in foam.

This application is writen in Python 3 (and uses some Python packages).
So, it is supposed to run on Windows, Linux and Mac.
It uses a graphical user interface and is quite easy to use. 

The CNC has to run a 4 axis version of GRBL version 1.1 if you want to control the CNC (home, move, ...) within the application.
Otherwise, you can also use the application to generate the Gcode and run it from another CNC controller. 

The easiest/cheapest solution for running GRBL 1.1 is to use an arduino mega combined with a RAMP 1.x board.
A GRBL version running on this hardware is in this github site. It is a fork from a GRBL made by fra589 (https://github.com/fra589/grbl-Mega-5X/tree/edge/grbl) 

An alternative could be to use a version of GRBL running a STM32F103 (blue pill). This can be connected to a RAMP 1.x or directly to drivers like TB6600. Such a GRBL version is available on this Github site too as a separate project. 

In this python application you can
- define the characteristics of your table (dimension, speed, com port, baudrate, ...)
- define the characteristics of some material (high/low speeds, radiances, normal cutting speed)
- upload ".dat" files for root and tip profiles
- transform the profiles (chords, thickness, incidence, inverse, skin covering, smoothing, reducing points, ...)
- add/modify synchronisation points for complex profiles
- define the dimensions and the position of the bloc on the table
- directly control the CNC hot wire (connect to Grbl, unlock GRBL, Home, Move the 4 axis, make vertical/horizontal.inclined cuts, apply heat,...)
- generate and save the gcode for cutting the profiles in the foam
- generate Gcode to cut rectangular spar, circular slot, triangular cut for aileron
- send the generated gcode to GRBL
- save and reload previous projects, tables, materials
- allows to import profiles having been created/modified by the powerful profile editor named complexes.exe

Note: at startup, the program tries to upload a project named "startup.ini" (in the same directory).
You can just save one of your project under this name, if you want to use this project as default (including the table and matterial set up)  

For Windows 10 64 bits, a full compiled version is available as an .exe on github in the "dist" forlder.
This version can be run without installing other packages.
Some users says that it could run on oldier version of Windows too

In order to run the application on other operating systems, you have to install:
- python 3 latest version ( I tested it with version 3.7)
- mathplotlib latest version
- numpy
- configparser
- shapely (not sure it is really needed)
- scipy
- pyserial
- pyQt5
- pyqtgraph
- time  (normally already included in python)
- threading (normally already included in python)
- atexit (normally already included in python)
- queue (normally already included in python)

Here some screen shots (perhaps not the latest version but it gives a good idea of the functionalities)

![Profil](https://github.com/mstrens/Hot_wire_QT/blob/main/image/Profil.png)

![Transform](https://github.com/mstrens/Hot_wire_QT/blob/main/image/Transform.png)

![Bloc](https://github.com/mstrens/Hot_wire_QT/blob/main/image/Bloc.png)

![Material](https://github.com/mstrens/Hot_wire_QT/blob/main/image/Material.png)

![Guillotine](https://github.com/mstrens/Hot_wire_QT/blob/main/image/Guillotine.png)

![Cut_project](https://github.com/mstrens/Hot_wire_QT/blob/main/image/Cut%20project%20Top%20view.png)

![Cut_project](https://github.com/mstrens/Hot_wire_QT/blob/main/image/Cut%20project%20RootTip%20view.png)

![Cut_project](https://github.com/mstrens/Hot_wire_QT/blob/main/image/Cut%20spar.png)

![Table](https://github.com/mstrens/Hot_wire_QT/blob/main/image/Table.png)
