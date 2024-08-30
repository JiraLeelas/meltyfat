import cv2
import os
import numpy as np
import string

class WellAnalyzer:
    """
    Class to analyze and get thermal values from pandas dataframe.
    """
    def __init__(self, reference_image_path=None, detected_wells_dict=None):
        self.reference_image_path = reference_image_path
        self.image = None
        self.detected_wells_dict = detected_wells_dict
        
        ## Auto load image
        if self.reference_image_path:
            self.load_image(self.reference_image_path)

        ## After applying map_well_ids()
        self.mapped_wells = []
    
    def load_image(self, reference_image_path):
        if not os.path.exists(reference_image_path):
            raise FileNotFoundError("Error: Image file not found")
        self.image = cv2.imread(reference_image_path)
        if self.image is None:
            raise ValueError("Error: Could not load image")
        print("Success: Image loaded")
    
    def set_image(self, image):
        if image is None:
            raise ValuseError("Error: No image provided.")
        self.image = image
        print("Success: Image set")
    
    def set_detected_dict(self, detected_wells_dict):
        self.check_detected_dict(detected_wells_dict)
        self.detected_wells_dict = detected_wells_dict

    def check_detected_dict(self, detected_wells_dict):
        ## Check list type
        if not isinstance(detected_wells_dict, list):
            raise ValueError("Error: Must be a list of dicts.")
        
        ## Check each dict data
        for a_well_data in detected_wells_dict:
            if not isinstance(a_well_data, dict):
                raise ValueError("Error: Each detected wells must be a dictionary.")
            if ("well_center" or "well_data" or "confidence") not in a_well_data:
                raise ValueError(f"Error: Unmatched structure. Must inlude 'well_center', 'well_radius', and 'confidence'.")
    
    ### Functions to interact with the well
    def map_well_ids(self, invert_image=False):
        """
        This function map and assign unique ids for each well in 96-well plate format.
        There is an option to invert the image. This means that from mapping A01, A02, ..., A12, 
        it will map the first row as H12, H11, H10, ..., H02, H01 instead.
        """
        row_names = list(string.ascii_uppercase[:8]) # 'A -> H'

        if invert_image:
            row_names = row_names[::-1] # Invert to 'H -> A'
        sorted_by_coordinates = sorted(self.detected_wells_dict, key=lambda k: k["well_center"]) # Sorted by coordinates
        for well_column_idx in range(12):  # From column '1 -> 12'

            ## Column start and end
            ## Ex: col 1 -> start 0, end 8 -> [0, ..., 7]
            ## Ex: col 2 -> start 8, end 16 -> [8, ..., 11]
            start_idx = 8 * well_column_idx 
            end_idx = 8 * (well_column_idx + 1)
            sorted_by_row = sorted(sorted_by_coordinates[start_idx:end_idx], key=lambda k: k["well_center"][1])  # Sort wells by row
            
            for well_row_idx, current_well in enumerate(sorted_by_row):  # Loop 8 rows
                if invert_image:
                    well_id = row_names[well_row_idx] + f"{12 - well_column_idx:02d}" # Well id from H12 to A1
                    well_column = 12 - well_column_idx
                else:
                    well_id = row_names[well_row_idx] + f"{well_column_idx + 1:02d}" # Well id from A1 to H12
                    well_column = well_column_idx + 1
                    
                self.mapped_wells.append({
                    "well_id": well_id,
                    "well_row": row_names[well_row_idx],
                    "well_column": well_column,
                    "well_center": current_well["well_center"],
                    "well_radius": current_well["well_radius"],
                    "confidence": current_well["confidence"]
                }) 
        return self.mapped_wells
    
    def map_sensor_coordinate(self, sensor_temp_df, x_coor, y_coor):
        """
        Get image coordinates as "x" and "y" and map into sensor coordinates.

        ------ HIKMICRO Pocket 2 ------
        Description             W x H
        Image Dimensions        640x480
        Sensor Dimensions       256x192
        -------------------------------
        """
        ## Get dimension details
        img_height, img_width, color_channels = self.image.shape # Reference Image
        sensor_height, sensor_width = sensor_temp_df.shape # Data frame

        ## Map the image coordinates into sensor coordinates
        x_scale = sensor_width / img_width
        y_scale = sensor_height / img_height
        sensor_x = int(x_coor * x_scale)
        sensor_y = int(y_coor * y_scale)

        return sensor_x, sensor_y
    
    @staticmethod
    def get_sensor_temp(sensor_temp_df, x_coor, y_coor, detect_window=0, precision=2):
        """
        This function extract temperatures out of sensor_df by mapping image coordinates into sensor range.
        """
        ## Define params
        avg_well_temp = None
        sd_well_temp = None
        detect_window_limit = 5
        detect_window = min(max(detect_window, 0), detect_window_limit) # set boundary

        if (x_coor or y_coor) < 0 or (x_coor >= sensor_temp_df.shape[1] or y_coor >= sensor_temp_df.shape[0]):
            raise ValueError("Error: Provided coordinates are out of bounds.")

        ## Define Slice Boundaries
        start_x = max(0, x_coor - detect_window)
        end_x = min(sensor_temp_df.shape[1], x_coor + detect_window + 1)
        start_y = max(0, y_coor - detect_window)
        end_y = min(sensor_temp_df.shape[0], y_coor + detect_window + 1)

        sensor_window = sensor_temp_df.iloc[start_y:end_y, start_x:end_x]

        ## Remove Outliers base on IQR 
        Q1 = sensor_window.quantile(0.25) # Q1 Lower
        Q3 = sensor_window.quantile(0.75) # Q2 Upper
        IQR = Q3 - Q1
        lower_bound = Q1 - (1.5 * IQR)
        upper_bound = Q3 + (1.5 * IQR)

        filtered_sensor_window = sensor_window[(sensor_window >= lower_bound) & (sensor_window <= upper_bound)].dropna()

        ## Apply stack() as it is a matrix
        avg_well_temp = round(filtered_sensor_window.stack().mean(), precision)
        sd_well_temp = round(filtered_sensor_window.stack().std(), precision)

        return avg_well_temp, sd_well_temp
    
    @staticmethod
    def create_well_ids():
        """
        Generate well ids list from [A1, A2, ..., H11, H12]
        """
        rows = list(string.ascii_uppercase[:8])
        cols = list(range(1, 13))
        wellplate_ids = [f"{row}{col}" 
            for row in rows
            for col in cols
            ]
        return wellplate_ids


    