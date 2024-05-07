#!/bin/bash

cd "$(dirname "$0")"
echo "Installing required packages. This will take a while..."
pip3 install -r requirements.txt
clear
python3 chat.py
read -p "Press Enter to exit..."
