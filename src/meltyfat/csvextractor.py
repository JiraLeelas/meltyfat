import csv
from itertools import islice
import re
import os
import shutil
import pandas as pd
from datetime import datetime, timedelta

class HikExcelExtractor:
    """
    Class of HikExcelExtractor to intereact with HIKMICRO VDO CSV file format.

    Usage:
        Create object -> apply map_csv() -> get_sampled_data() / save_sampled_data()
    """
    def __init__(self, vdo_csv, sample_sec=30):
        ## Default Parameters
        self.encoding = "utf-8-sig"
        self.sensor_pixel_nrows = 192

        ## User Input
        self.vdo_csv = vdo_csv
        if not self.check_vdo_csv():
            raise ValueError("Error: Uable to load or Invalid format.")
        self.sample_sec = self.check_sample_sec(sample_sec)

        ## Extract
        self.ref_tst = None
        self.sensor_frame_ls = []
        self.sampled_frames = []
    
    @staticmethod
    def check_sample_sec(sample_sec, default_sample_sec = 30):
        try:
            sample_sec = int(sample_sec)
            if sample_sec > 0:
                return sample_sec
            else:
                raise ValueError("Sample seconds must be greater than zero.")
        except ValueError:
            print("Error: Invalid sampling seconds provided. Using {default_sample_sec} seconds")
            return default_sample_sec

    def check_vdo_csv(self):
        """
        Check: exist -> CSV -> Structure -> True

        - - - - - XLS STRUCTURE - - - - - 
        ROW            DATA
        [0] Temperature, Celsius Degree
        [1]
        [2] Image
        [3]
        [4] time:2024/05/10 12:45:46.205
        [5] 23.8, 24, ... , 24.7, 25
        - - - - - - - - - - - - - - - - - 
        """
        ## Check Exist
        if not os.path.isfile(self.vdo_csv):
            print("Error: File does not exist.")
            return False
        
        ## Check If CSV
        if not self.vdo_csv.endswith(".csv"):
            print("Error: File must be in CSV fomat.")
            return False

        ## Check File Format
        num_sample_lines = 10
        sample_lines = []

        try:
            with open(self.vdo_csv, mode="r", encoding=self.encoding) as file:
                extracted_lines = list(islice(file, num_sample_lines))
                for line in extracted_lines:
                    if line.startswith("\ufeff"): # Remove Byte Order Mark
                        line = line[1:]
                    sample_lines.append(line.strip())
        
        except FileNotFoundError:
            print("Error: File Not Found.")
            return False
        
        ## Check Structure
        tst_pattern = r"time:\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}\.\d{3}\s*"
        check_temp = sample_lines[0].split(",")[0].strip() == "Temperature Unit :"
        check_image = str(sample_lines[2].strip()) == "Image"
        check_timestamp = bool(re.match(tst_pattern, "time:2024/06/19 15:53:42.550"))

        if not (check_temp and check_image and check_timestamp):
            print("Error: Invalid File Format")
            return False
        return True

    def get_timestamp(self, vdo_tst):
        """
        This function extract timestamp within the .xls file
        TST FORMAT: 'time:2024/05/10 12:45:46.205'
        """
        tst_pattern = r"time:(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}\.\d{3})"
        match = re.search(tst_pattern, vdo_tst)
        if match:
            tst_part = match.group(1)
            timestamp = datetime.strptime(tst_part, "%Y/%m/%d %H:%M:%S.%f")
            return timestamp
        else:
            print("Error: No timestamp found")
            return None

    def tst_delta_seconds(self, tst, ref_tst):
        """
        Time difference in seconds
        """
        delta = tst - ref_tst 
        return delta.total_seconds()

    def nearest_norm_tst(self, tst_ls, target_sec):
        """
        Get the nearest normalized seconds.
        Example:
            ref_sec = 30
            tst_ls["normalized"] = 0.0, ..., 29.981, 30.181
            The algorithm will register 29.981 as the nearest
        """
        nearest_tst = None
        smallest_diff = float("inf")
        for frame in tst_ls:
            diff = abs(frame["normalize"] - target_sec)
            if diff < smallest_diff:
                smallest_diff = diff
                nearest_tst = frame # Dict
        return nearest_tst

    def sample_norm_tst(self, tst_ls):
        sampled_frames = []
        norm_start = 0.0 # Starter
        target_norm_sec = norm_start # Starter from 0.0 + sample_sec
        while target_norm_sec <= tst_ls[-1]["normalize"]: # Boundary is the last normalized seconds
            nearest_frame = self.nearest_norm_tst(tst_ls, target_norm_sec)
            if nearest_frame:
                # print(nearest_frame)
                sampled_frames.append(nearest_frame)
            target_norm_sec += self.sample_sec
        return sampled_frames

    def extract_dt(self, dt):
        """
        This function extracts datetime into date part and time part and round up microseconds part.
        """
        if not isinstance(dt, datetime):
            raise TypeError(f"Expected a datetime object, but get {type(dt).__name__}.")
        date_part = dt.date()
        if dt.microsecond >= 500000:
            dt += timedelta(seconds=1)
        time_part = dt.time().replace(microsecond=0)
        return date_part, time_part

    def map_csv(self, sample_sec=None):
        """
        Map the location of timestamp and row to be extracted.
        """
        ## let users to update sample seconds without calling the class again
        if sample_sec != None:
            self.sample_sec = self.check_sample_sec(sample_sec)

        with open(self.vdo_csv, mode="r", encoding=self.encoding) as file:
            counter = 0
            tst_pattern = r"time:\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}\.\d{3}\s*"

            ## Loop to map location of timestamp and row
            for idx, line in enumerate(file):
                ## Data is a "csv", we want to get the location of tst.
                first_col = line.strip().split(",")[0].strip()

                ## If match with timestamp
                if re.match(tst_pattern, first_col):
                    if counter == 0:
                        self.ref_tst = self.get_timestamp(first_col)
                    sensor_frame_dct = {
                        "timestamp": self.get_timestamp(first_col),
                        "normalize": self.tst_delta_seconds(self.get_timestamp(first_col), self.ref_tst),
                        "index": idx, # csv index
                        "frame": counter # frame count
                    }
                    # print(sensor_frame_dct)
                    self.sensor_frame_ls.append(sensor_frame_dct)
                    counter += 1

        ## Extract Data from specific frames using normalized data.
        self.sampled_frames = self.sample_norm_tst(self.sensor_frame_ls)

    def get_sampled_data(self):
        """
        Get the map sample data points into a list of dictionaries.
        """
        ## User must map CSV first
        
        if not self.sampled_frames:
            print("Error: No Sampled Data Available. Please run map_csv first.")
            return None

        extracted_frames_ls = []

        for a_frame in self.sampled_frames:
            # print(a_frame)
            temp_df = pd.read_csv(
                self.vdo_csv,
                skiprows=a_frame["index"] + 1,
                nrows=self.sensor_pixel_nrows,
                delimiter=",",
                header=None
            )
            temp_df = temp_df.iloc[:, :-1] # Remove the last column
            date_part, time_part = self.extract_dt(a_frame["timestamp"])
            date_str = date_part.strftime("%Y-%m-%d")
            time_str = time_part.strftime("%H:%M:%S")

            frame_dict = {
                "date": date_str, # 2024-08-18
                "time": time_str, # 15:07:59
                "data": temp_df.values.tolist()
            }
            extracted_frames_ls.append(frame_dict)

        return extracted_frames_ls
    
    def save_sampled_data(self, save_dir):
        """
        Save the mapped data into a directory
        """
        ## User must map CSV first
        if not self.sampled_frames:
            print("Error: No Sampled Data Available. Please run map_csv() first.")
            return None
        ## Create save directory
        try:
            if not os.path.exists(save_dir):
                os.makedirs(save_dir, exist_ok=True)

            for a_frame in self.sampled_frames:
                # print(a_frame)
                temp_df = pd.read_csv(
                    self.vdo_csv,
                    skiprows=a_frame["index"] + 1,
                    nrows=self.sensor_pixel_nrows,
                    delimiter=",",
                    header=None
                )
                temp_df = temp_df.iloc[:, :-1] # Remove the last column
                date_part, time_part = self.extract_dt(a_frame["timestamp"])
                date_str = date_part.strftime("%Y%m%d")
                time_str = time_part.strftime("%H%M%S")

                filename = f"{date_str}_{time_str}_thm.csv"
                file_save_path = os.path.join(save_dir, filename)
                if os.path.exists(file_save_path): # check if already exist
                    os.remove(file_save_path)  # Remove the existing file before save new

                temp_df.to_csv(file_save_path, index=False)
        except:
            print("Error: Error while saving data")
        
        ## If everything passes
        print(f"Success: Saved to {save_dir}")

## Debugging
# if __name__ =="__main__":
#     sample_csv = "C:\\Users\\jleel\\Documents\\Project - Jira\\tempExtraction\\meltyfat\\meltyfat\\sample\\HM20240510122451_video_Temperature Value.csv"
#     save_dir = "C:\\Users\\jleel\\Documents\\Project - Jira\\tempExtraction\\meltyfat\\meltyfat\\test"
#     extractor = HikExcelExtractor(vdo_csv=sample_csv, sample_sec=30)
#     extractor.map_csv()
#     frames = extractor.get_sampled_data()
#     type(frames)
#     extractor.save_sampled_data(save_dir=save_dir)