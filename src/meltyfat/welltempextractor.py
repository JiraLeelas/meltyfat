import os
import torch
import string
import re
import csv
import cv2
import shutil
from itertools import islice
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from ultralytics import YOLO

## Class files
from .csvextractor import HikExcelExtractor # Get CSVs or List of dicts from VDO
from .welldetector import WellDetector # Detect and get arrays
from .wellanalyzer import WellAnalyzer # 96 well plate functions
from .datamanager import HikDataManager # Manages HIK sensor data

class WellTempExtractor:
    def __init__(self, ref_image_path, detected_wells, frame_dataORpath, output_path, detect_window=3, image_invert_status=False, output_filename=None):
        """
        Normally image is inverted, thus image_invert_status = True
        """
        self.ref_image_path = None # clearest image
        self.image_invert_status = False # bool
        self.detected_wells = None # detected wells list
        self.frame_dataORpath = None # Frame list of dicts or CSV Folder
        self.detect_window = 3
        self.output_path = None # output file save directory
        self.output_filename = None

        ## Class Process
        self.labelled_wells = None # Required
        self.frames_data_list = [] # Required
        ## Extraction results
        self.extracted_well_data = []

        ## Setters
        self.set_ref_image_path(ref_image_path)
        self.set_invert_status(image_invert_status)
        self.set_refCoordinates(detected_wells) # get detected wells and labelled
        self.set_detect_window(detect_window)
        self.set_frame_data(frame_dataORpath)
        self.set_output_filename(output_filename)
        self.set_output_path(output_path)
    
    def set_ref_image_path(self, a_path):
        if HikDataManager.check_path_exist(a_path):
            self.ref_image_path = a_path
        else:
            raise FileExistsError("Error: Invalid reference image path.")

    def set_invert_status(self, image_invert_status):
        """
        Set invert status, default is False
        """
        if not isinstance(image_invert_status, bool):
            raise ValueError("Error: Invert status must be a boolean.")
        self.image_invert_status = image_invert_status
    
    def set_refCoordinates(self, detected_wells_list):
        """
        In the case that user run the WellDetector and got a list of dicts.
        Store it in self.ref_coordinates
        """
        if WellDetector.check_detect_dict_list(detected_wells_list):
            self.detected_wells = detected_wells_list
            wellplate = WellAnalyzer(detected_wells_dict=self.detected_wells)
            self.labelled_wells = wellplate.map_well_ids(invert_image=self.image_invert_status)

        else:
            raise ValueError("Error: Provided detected wells list is in unsupported format.")

    def set_detect_window(self, detect_window):
        detect_window_limit = 5
        if isinstance(detect_window, int) and (0 <= detect_window <= detect_window_limit):
            self.detect_window = detect_window
        else:
            raise ValueError("Error: Detected Window must between 0 and 5.")

    def set_frame_data(self, frame_dataORpath):
        """
        This function provides userflexibility in providing either a list of dicts or a path to frames csv.
        """
        if isinstance(frame_dataORpath, list):
            self.set_frameList(frame_dataORpath)
        elif isinstance(frame_dataORpath, str): # Path
            self.set_frameFromCSVs(folder_path=frame_dataORpath)
        else:
            raise ValueError("Error: Provided frame must be a list of dicts or a folder of extracted frames.")
    
    def set_frameList(self, extracted_frames_list):
        """
        In the case that user run the CSV extractor and got a list of dicts.
        Store it in self.frames_data_list.
        """
        ## Check the provided data
        if HikDataManager.check_frame_dict_list(extracted_frames_list):
            self.frames_data_list = extracted_frames_list
        else:
            raise ValueError("Error: Provided frames list is in unsupported format.")
        
    def set_frameFromCSVs(self, folder_path=None):
        """
        Get sensor data from CSV either single file or multiple files.
        Store it in self.frames_data_list.
        """
        ## list all the CSV from the provided directory
        csv_frame_list = HikDataManager.get_CSVfromPath(folder_path)

        ## Run through all the files
        for a_frame in csv_frame_list:

            ## Extract Meta Data from filename
            sensor_fname = os.path.splitext(os.path.basename(a_frame))[0]
            creation_date, creation_time = sensor_fname.split("_")[0], sensor_fname.split("_")[1]
            formatted_date = f"{creation_date[:4]}-{creation_date[4:6]}-{creation_date[6:]}"
            formatted_time = f"{creation_time[:2]}:{creation_time[2:4]}:{creation_time[4:]}"
            # print(formatted_date, formatted_time)

            ## Get sensor data
            sensor_frame_df = HikDataManager.get_sensor_csv(a_frame, skip_rows=1)

            ## Format as dict
            frame_dict = {
                    "date": formatted_date, # 2024-08-18
                    "time": formatted_time, # 15:07:59
                    "data": sensor_frame_df.values.tolist()
                }
            
            ## Append
            self.frames_data_list.append(frame_dict)
    
    def set_output_path(self, a_path):
        if HikDataManager.check_path_exist(a_path):
            self.output_path = a_path
        else:
            raise FileExistsError("Error: Invalid output path.")
    
    def set_output_filename(self, a_name=None):
        if a_name:
            self.output_filename = a_name.replace(" ", "_")
        else:
            current_tst = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_filename = f"{current_tst}_extracted.csv" # YYYYMMDD_HHMMSS_extracted

    def get_ref_img_path(self):
        return self.ref_image_path

    def get_invert_status(self):
        return self.image_invert_status

    def get_detected_wells(self):
        return self.detected_wells
    
    def get_detect_window(self):
        return self.detect_window

    def get_output_path(self):
        return self.output_path

    def get_output_filename(self):
        return self.output_filename

    def get_labelled_wells(self):
        return self.labelled_wells
        
    def get_frame_data_list(self):
        return self.frames_data_list

    ### Extraction and export functions
    def run_TempExtract(self):
        """
        This function run temperature extractor as a full program.
        Start: Provide image, a folder of sensor frame
        Finish: Extract a CSV file
        """
        ## Initialize sensor
        wellplate = WellAnalyzer(reference_image_path=self.ref_image_path)

        ## Create Headers and contatiners for data
        # header_row = ["Date", " Time"] + WellAnalyzer.create_well_ids()
        # detected_data_rows = []

        ## run through the data
        for a_frame in self.frames_data_list:
            date_detected = a_frame["date"]
            time_detected = a_frame["time"]
            data_detected = a_frame["data"] # as a list
            data_df = pd.DataFrame(data_detected) # Convert into dataframe
            
            frame_detected_wells = dict() # for this frame

            for a_well in self.labelled_wells:
                
                ## Format name from A01 to A1
                # well_id = a_well["well_id"]
                well_row = a_well["well_id"][0]
                well_col = int(a_well["well_id"][1:])
                well_id = f"{well_row}{well_col}"

                well_coordinate = a_well["well_center"]
                sensor_x, sensor_y = wellplate.map_sensor_coordinate(data_df, well_coordinate[0], well_coordinate[1])
                avg_well_temp, sd_well_temp = WellAnalyzer.get_sensor_temp(data_df, sensor_x, sensor_y, detect_window=self.detect_window, precision=2)
                frame_detected_wells[well_id] = avg_well_temp
            
            # sorted_wells = dict(sorted(frame_detected_wells.items(), key=lambda item: (item[0], int(item[0][1:])))) # A01
            sorted_wells = dict(sorted(frame_detected_wells.items(), key=lambda item: (item[0][0], int(item[0][1:])))) # A1
            row_data = {
                "Date": date_detected,
                "Time":time_detected,
                **sorted_wells
            }
            self.extracted_well_data.append(row_data)
    
    def get_extractedDF(self):
        if not self.extracted_well_data:
            print("Error: No data available to export. Please run_TempExtract().")
            return None
        extracted_df = pd.DataFrame(self.extracted_well_data)
        return extracted_df

    def get_extractedCSV(self):
        if not self.extracted_well_data:
            print("Error: No data available to export. Please run_TempExtract().")
            return None
        ## Create output filename
        output_file_path = os.path.join(self.output_path, self.output_filename)

        ## If the exact filename already exist remove it
        if os.path.exists(output_file_path):
            os.remove(output_file_path)
        
        ## Exported
        extracted_df = pd.DataFrame(self.extracted_well_data)
        extracted_df.to_csv(output_file_path, index=False)

        print(f"Success: Exported to {output_file_path}")


