# meltyfat
A proof-of-concept Python package for detection and extraction of HIKMICRO Pocket 2 radiometric thermography image on 96-well plate for a high-throughput studies of material thermal properties. This package is designed to work with the [hik-thermo-dashboard](https://github.com/JiraLeelas/hik-thermo-dashboard) visualization website. The training dataset, model trainining scripts, and example data are provided in [Online Dissertation Resources](https://drive.google.com/drive/folders/1S2j5NRCx6h3Wx6Jc4qjrtIDGvs91A9j0?usp=drive_link), which is being hosted on Google Drive.

## Project Motivation
This project aims to demonstrate a proof of concept data acquisition ecosystem for a high-throughput and low-cost thermal gradient system based on 96-well plate architecture. This system can be applied for a wide range of applications in studying the thermochemical (e.g., thermal decomposition) and thermophysical properties of materials. The thermal gradient heating and cooling system is developed by [Dr Richard Thompson](https://www.durham.ac.uk/staff/r-l-thompson/) research unit at the Durham University, United Kingdom. The proposed data acquisition ecosystem consist of two major parts: data extraction program and a webbased dashboard system.

This github repositatry is the first part of the purposed ecosystem that is used to extracted data from the thermal infrared camera for this in this proof-of-concept system. This module provide users with the option to detect each individual well within the well plate using either Hough Circle Transform or a custom trained YOLOv8 object detection model.

## Development Tools
- Programming Language: Python
- Coding Paradigm: Object-oriented programming (OOP)
- Libraries: PyTorch, Pandas, NumPy, Ultralytics (YOLOv8), OpenCV, Matplotlib




