#!/bin/bash
clear
echo "People counter by Zajac & Wieczorek"
source ~/.profile
workon cv  
python ~/COUNTER/rpi-people-counter/counter.py
