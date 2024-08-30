import os
import re
import csv
import pandas as pd

class HikDataManager:
    """
    This class contains static methods to manage and read thermal sensor data.
    It supports HIKMICRO Pocket 2 model.
    """
    @staticmethod
    def check_path_exist(a_path):
        return os.path.exists(a_path)

    @staticmethod
    def check_fname(fname):
        """
        Check for the filename format.
        return
            True -> follow Hik naming format
            False -> does not follow
        """
        hik_fname_format = r"\d{8}_\d{6}_thm\.csv"
        return re.match(hik_fname_format, fname) is not None

    @staticmethod
    def check_isCSV(a_path):
        """
        Check if the provided path is a CSV
        return
            True -> single csv path
            False -> others
        """
        path_fname = os.path.basename(a_path) # get filename
        return os.path.isfile(a_path) and a_path.endswith(".csv") and HikDataManager.check_fname(a_path)

    @staticmethod
    def get_listOfCSVs(folder_of_frames):
        """
        Get list of CSV files from a folder.
        CSV file must have specific name format

        Folder Naming:
            YYYYMMDD_hhmmss_thm.csv
        """
        print(folder_of_frames)
        csv_files = [os.path.join(folder_of_frames, f) for f in os.listdir(folder_of_frames) if HikDataManager.check_fname(f)]
        return sorted(csv_files) if csv_files else None
    
    @staticmethod
    def get_CSVfromPath(a_path):
        """
        Get a list of CSVs from a path.
        return:
            a list of CSVs
        """
        if not os.path.exists(a_path):
            raise FileNotFoundError("Error: Provided path does not exist.")
        # print("Path Exists")
        ## Check if its either a single CSV file or a list of CSVs
        if HikDataManager.check_isCSV(a_path):
            # print("Single File")
            return [a_path] # single CSV
        elif os.path.isdir(a_path):
            # print("Multiple Files")
            return HikDataManager.get_listOfCSVs(a_path)
        else:
            raise ValueError("Error: Provided path must be a CSV file of a directory of CSVs")

    @staticmethod
    def get_sensor_list(sensor_temp_list):
        """
        From CSV extractor
        [{
            "date": date_str,
            "time": time_str,
            "data": temp_df.values.tolist()
        }]
        """
        sensor_temp_df = pd.DataFrame(data_list)
        return sensor_temp_df
    
    @staticmethod
    def get_sensor_csv(sensor_csv, skip_rows=0):
        """
        Normally skip_row = 1 as the file extracted as the first row is only index

        ------ 20240510_122452_thm ------
        0, 1, 2, 3, 4, ..., 255
        24.5, 24.4, 24.6, ..., 25.9
        ---------------------------------
        """
        sensor_temp_df = pd.read_csv(
            sensor_csv,
            header = None,
            skiprows = skip_rows
        )
        sensor_temp_df = sensor_temp_df
        # sensor_temp_df = sensor_temp_df.iloc[:, :-1] # Remove last column
        return sensor_temp_df
    
    @staticmethod
    def check_frame_dict(a_frame_dict):
        """
       Single dict Format
        {
        "date": date_str,
        "time": time_str,
        "data": temp_df.values.tolist()
        }
        """
        frame_dict_keys = ["date", "time", "data"] # Required
        date_pattern = r"\d{4}-\d{2}-\d{2}" # 2024-08-18
        time_pattern = r"\d{2}:\d{2}:\d{2}" # 15:40:59

        if not all(key in a_frame_dict for key in frame_dict_keys):
            return False
        if not re.match(date_pattern, a_frame_dict["date"]):
            return False
        if not re.match(time_pattern, a_frame_dict["time"]):
            return False
        if not isinstance(a_frame_dict["data"], list): 
            return False
        return True
    
    @staticmethod
    def check_frame_dict_list(frames_list):
        """
        Apply this to all list of frame dicts
        """
        return all(HikDataManager.check_frame_dict(a_frame) for a_frame in frames_list)
    
    # @staticmethod
    # def create_CSV(output_file_path, csv_header, data_rows):
    #     with open(output_file_path, "w", newline="") as file:
    #         csv_writer = csv.writer(file)
    #         csv_writer.writerow(csv_header)
    #         csv_writer.writerows(data_rows)

# if __name__ == "__main__":
#     frames_folder = "C:\\Users\\jleel\\Documents\\Project - Jira\\tempExtraction\\meltyfat\\meltyfat\\data\\framedump"
#     frame_csvs = HikDataManager.get_listOfCSVs(frames_folder)
#     print(frame_csvs)