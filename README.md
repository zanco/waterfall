# waterfall
waterfall python script for rtl_power output

started with:


rtl_power -d 0 -f 430M:440M:4k -g 9 -p 57 -i 30  -c 50% | python2 waterval435.py 430000000 2441.41 4096 8

where the values 2241.41 4096 and 8 stand for logged fft bin size, logged fft bins and number of frequency hops, all shown as output from the rtl_power command while run without the piping to the python file.

rtl_power -d 0 -f 430M:440M:4k -i 30 -c 50%
No supported devices found. (this was just a dry testrun)
Number of frequency hops: 8
Dongle bandwidth: 2500000Hz
Downsampling by: 1x
Cropping by: 50.00%
Total FFT bins: 8192
Logged FFT bins: 4096
FFT bin size: 2441.41Hz
Buffer size: 16384 bytes (3.28ms)
Reporting every 30 seconds

So, remember, while changing the frequency bandwidth you have to change the last 3 values while piping to waterval435.py 

examples can be viewed at https://www.pe2bz.nl/hamradio/skymonitor/rtlsat_power.png and https://www.pe2bz.nl/hamradio/skymonitor/rtlTest_power.png
