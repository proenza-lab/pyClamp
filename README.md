# pyClamp
## A fast graphical user interface for the [dyClamp](https://github.com/christianrickert/dyClamp) sketch

**[pyClamp](https://github.com/christianrickert/pyClamp)** is a feature-complete graphical user interface written in Python to demonstrate the flexibility of the novel dynamic clamp implementation: The current user interface focuses on data consistency (between the interface and the dynamic clamp system) and data transparency (with the option of monitoring any values live). Furthermore, a lab journal will keep track of new experiments and write all relevant settings with corresponding timestamps.

**[dyClamp](https://github.com/christianrickert/dyClamp)** is a further development of the [dynamic_clamp](https://github.com/nsdesai/dynamic_clamp) sketch with a focus on a robust serial communication between the Teensy and its controlling host computer.

![Screenshot](https://github.com/christianrickert/pyClamp/blob/master/media/pyClamp.png)

## Data consistency

When uploading conductance values or calibration parameters to the Teensy, the user interface checks the status of the transmissions with the Teensy's command echos. If a transmission failure is detected, an error message will be displayed in the status field and the current values will be downloaded from the Teensy. A green background indicator then highlights all up-to-date values. In addition, all values that have exclusively been changed in the user interface - but have not yet been uploaded - are indicated by a white background. Furthermore, incorrect entries (with letters or invalid characters) are highlighted in red, while all transmission buttons are temporarily disabled.

## Data transparency

The live reports feature allows users to monitor any values on the Teensy live. To demonstrate this feature, the latest values of the membrane potential, the injected current, and the cycle time are visualized every 20 ms. When implementing new current models or defining new trigger events, the live reports will help with debugging and understanding the dynamic clamp setup.

## Lab journal

Every time an experiment is started (Start button), a new lab journal entry is created. The new entry contains the start time, the present conductance values, and the calibration parameters. Once the experiment is stopped (Stop button), the entry is finalized with a corresponding timestamp.

Example:
```
Experiment started:	Sun Mar 31 19:04:24 2019
G_Shunt	[nS]    	     1.00
G_H 	[nS]       	     0.00
G_Na	[nS]       	     0.00
OU1_m	[nS]      	     0.00
OU1_D	[nS^2/ms] 	     0.00
OU2_m	[nS]      	     0.00
OU2_D	[nS^2/ms] 	     0.00
G_EPSC	[nS]     	     0.00
AMP_i	[mV/mV]   	    50.00
AMP_o	[pA/V]    	   400.00
ADC_m	[mV/1]    	     5.50
ADC_n	[mV]      	-11500.00
DAC_m	[1/pA]    	   750.00
DAC_n	[0-4095]  	  2000.00
VLT_d	[mV]      	     0.00
Experiment stopped:	Sun Mar 31 19:07:01 2019
```
