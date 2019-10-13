# pyClamp
## A live graphical user interface for the [dyClamp](https://github.com/christianrickert/dyClamp) sketch

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.2825278.svg)](https://doi.org/10.5281/zenodo.2825278)

**[pyClamp](https://github.com/christianrickert/pyClamp)** is a feature-complete graphical user interface written in Python to demonstrate the flexibility of the novel dynamic clamp implementation: The current user interface focuses on data consistency (between the interface and the dynamic clamp system) and data transparency (with the option of monitoring any values live). Furthermore, a lab journal will keep track of new experiments and record all relevant settings with corresponding timestamps.

**[Video demonstration](https://github.com/christianrickert/pyClamp/blob/master/media/pyClamp.mkv?raw=true)** :movie_camera: (6.5 MiB, [H.264/MPEG-4 AVC](https://en.wikipedia.org/wiki/H.264/MPEG-4_AVC)) of **[dyClamp](https://github.com/christianrickert/dyClamp)** and **[pyClamp](https://github.com/christianrickert/pyClamp)** producing and monitoring a current command for the Axopatch 200B amplifier.

**_Cross-reference_:** **[dyClamp](https://github.com/christianrickert/dyClamp)** is a further development of the [dynamic_clamp](https://github.com/nsdesai/dynamic_clamp) sketch with a focus on a robust serial communication between the Teensy and its controlling host computer.

![Screenshot](https://github.com/christianrickert/pyClamp/blob/master/media/pyClamp.png)

## Data consistency

When uploading conductance values or calibration parameters to the Teensy, the user interface checks the status of the transmissions with the Teensy's command echos. If a transmission failure is detected, an error message will be displayed in the status field and the current values will be downloaded from the Teensy. A green background indicator then highlights all up-to-date values. In addition, all values that have exclusively been changed in the user interface - but have not yet been uploaded - are indicated by a white background. Furthermore, incorrect entries (with letters or invalid characters) are highlighted in red, while all transmission buttons are temporarily disabled.

## Data transparency

The live reports feature allows users to monitor any values on the Teensy live. To demonstrate this feature, the latest values of the membrane potential, the injected current, and the cycle time are visualized every 20 ms. When implementing new current models or defining new trigger events, the live reports will help with debugging and understanding the dynamic clamp setup.

## Lab journal

Every time an experiment is started or modified (Start button), a new lab journal entry is created. The new entry contains the start time, the present conductance values, and the calibration parameters. Once the experiment is stopped (Stop button), the entry is finalized with a corresponding timestamp.

Example:
```
Experiment started:	Mon Apr  1 15:34:50 2019
G_Shunt	[nS]    	     0.00
G_H 	[nS]       	    20.00
G_Na	[nS]       	     0.00
OU1_m	[nS]      	     0.00
OU1_D	[nS^2/ms] 	     0.00
OU2_m	[nS]      	     0.00
OU2_D	[nS^2/ms] 	     0.00
G_EPSC	[nS]     	     0.00
AMP_i	[mV/mV]   	   100.00
AMP_o	[pA/V]    	  2000.00
ADC_m	[mV/1]    	     5.61
ADC_n	[mV]      	-12096.07
DAC_m	[1/pA]    	 33064.41
DAC_n	[0-4095]  	  1854.43
VLT_d	[mV]      	     0.00
Experiment started:	Mon Apr  1 15:35:05 2019
G_Shunt	[nS]    	     0.00
G_H 	[nS]       	    10.00
G_Na	[nS]       	     0.00
OU1_m	[nS]      	     0.00
OU1_D	[nS^2/ms] 	     0.00
OU2_m	[nS]      	     0.00
OU2_D	[nS^2/ms] 	     0.00
G_EPSC	[nS]     	     0.00
AMP_i	[mV/mV]   	   100.00
AMP_o	[pA/V]    	  2000.00
ADC_m	[mV/1]    	     5.61
ADC_n	[mV]      	-12096.07
DAC_m	[1/pA]    	 33064.41
DAC_n	[0-4095]  	  1854.43
VLT_d	[mV]      	     0.00
Experiment stopped:	Mon Apr  1 15:35:11 2019
```

## Software requirements

If you want to use **[pyClamp](https://github.com/christianrickert/pyClamp)** in your dynamic clamp setup, you can either download the bundled versions for Windows from the [releases page](https://github.com/christianrickert/pyClamp/releases) or run it directly from the source script. In the latter case, you'll need recent versions of [Python](https://www.python.org/downloads/), [NumPy](https://www.scipy.org/scipylib/download.html), [Matplotlib](https://matplotlib.org/users/installing.html), and [PySerial](https://pypi.org/project/pyserial/). However, the latest Windows versions of all of these extension packages can be downloaded from [Christoph Gohlke's repository](https://www.lfd.uci.edu/~gohlke/pythonlibs/). These are my version recommendations:

- Python      (>= 3.7.3)
- NumPy       (>= 1.16.2)
- Matplotlib  (>= 3.0.3)
- PySerial    (>= 3.4.0)

## Acknowledgements

I would like to thank [Cathy Proenza](http://www.ucdenver.edu/academics/colleges/medicalschool/departments/physiology/faculty/Pages/Proenza.aspx), [Alexander Polster](https://www.linkedin.com/in/alexanderpolster/), and [Andrew Scallon](https://optogeneticsandneuralengineeringcore.gitlab.io/ONECoreSite/) for providing resources and valuable feedback during the development process.

## Development & Bug reports

If you would like to participate in the development, please [fork this repository](https://help.github.com/articles/fork-a-repo) to your GitHub account. In order to report a problem, please create a [new issue](https://help.github.com/articles/creating-an-issue/) in this repository.

Your feedback is welcome! Please contact me at [GitHub](https://github.com/christianrickert/) or via [e-mail](mailto:mail@crickert.de).
