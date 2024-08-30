# meltyfat
A proof-of-concept Python package for detection and extraction of HIKMICRO Pocket 2 radiometric thermography image on 96-well plate for a high-throughput studies of material thermal properties. This package is designed to work with the [hik-thermo-dashboard](https://github.com/JiraLeelas/hik-thermo-dashboard) visualization website. The training dataset, model trainining scripts, and example data are provided in [Online Dissertation Resources](https://drive.google.com/drive/folders/1S2j5NRCx6h3Wx6Jc4qjrtIDGvs91A9j0?usp=drive_link), which is being hosted on Google Drive.

## Wells Dectection
This module provide users with the option to detect each individual well within the well plate using either Hough Circle Transform or a custom trained YOLOv8 object detection model.



