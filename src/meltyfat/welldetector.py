import torch
import os
import numpy as np
import cv2
from ultralytics import YOLO
import matplotlib.pyplot as plt

class WellDetector:
    ## Class Variable
    current_dir = os.path.dirname(os.path.abspath(__file__)) # Current directory
    default_model_rel_path = os.path.join(current_dir, "models", "small_lr0_early_stp.pt")

    def __init__(self, reference_img_path=None):
        self.device = "cuda" if torch.cuda.is_available() else "cpu" # Check device
        print(f"Device: {self.device}")
        self.image = None
        self.reference_img_path = reference_img_path
        if reference_img_path:
            try:
                self.load_image(reference_img_path=reference_img_path)
            except FileNotFoundError:
                print("Error: File not found")
        self.detected_method = None # Signature
        self.well_coordinates = []
    
    def reset_coordinates(self):
        self.well_coordinates = []
        self.detected_method = None
    
    def load_image(self, reference_img_path):
        """
        Load image from path as BGR image
        """
        if not os.path.exists(reference_img_path):
            raise FileNotFoundError("Error: Image file not found")

        self.image = cv2.imread(reference_img_path)
        if self.image is None:
            raise ValueError("Error: Could not load image")
        print("Success: Image loaded")
    
    def set_image(self, image):
        if image is None:
            raise ValuseError("Error: No image provided.")
        self.image = image
        print("Success: Image set")
    
    ## Detection Functions
    def detect_HoughCircles(self, dp=1, minDist=10, param1=200, param2=10, minRadius=12, maxRadius=14):
        if self.image is None:
            raise ValueError("Error: No set image. Please load image first.")
        self.reset_coordinates() # Reset coordinates
        self.detected_method = "Hough_Circle_Transform"

        ## Change to gray scale for easy detection
        gray_img = cv2.cvtColor(self.image, cv2.COLOR_BGR2GRAY)
        gray_img = cv2.GaussianBlur(gray_img, (3,3), 0) # add blur

        detected_circles = cv2.HoughCircles(
            gray_img, # img for detection
            cv2.HOUGH_GRADIENT, # detection method
            dp=dp, # inverse raito of resolution
            minDist=minDist,
            param1=param1,
            param2=param2,
            minRadius=minRadius,
            maxRadius=maxRadius
        )

        ## If detected
        if detected_circles is not None:
            # print("Detected")
            detected_circles = np.uint(np.around(detected_circles))
            for i in detected_circles[0, :96]: # 96 Well Plate Max circles is 96
                circle_center = (i[0], i[1])
                circle_radius = i[2]
                self.well_coordinates.append({
                    "well_center": circle_center,
                    "well_radius": circle_radius,
                    "confidence": None
                })
                
            ## Display Detection Result
            self.display_detected_wells()
            return self.well_coordinates
        else:
            print("Error: No circle wells were detected.")
            return None
            
    def detect_YOLOv8(self, model_path=default_model_rel_path, conf_threshold=0.25):
        if self.image is None:
            raise ValueError("Error: No set image. Please load image first.")
        self.reset_coordinates() # Reset coordinates
        self.detected_method = "YOLOv8_Custom_Model"

        model = YOLO(model_path) # load model
        results = model(self.image, conf=conf_threshold) # run detection

        for result in results:
            for box in result.boxes:
                x_min, y_min, x_max, y_max = box.xyxy[0].cpu().numpy()
                detect_conf = box.conf[0].cpu().numpy() # detection confidence
                center_x = int((x_min + x_max)/2)
                center_y = int((y_min + y_max)/2)
                width = int(x_max - x_min)
                height = int(y_max - y_min)
                circle_radius = int(min(width, height)/2)
                self.well_coordinates.append({
                    "well_center": (center_x, center_y),
                    "well_radius": circle_radius,
                    "confidence": f"{detect_conf:.2f}" # Detection Confidence
                })

        ## Display Detection Results
        self.display_detected_wells()
        return self.well_coordinates
    
    ## Display Detected Wells
    def display_detected_wells(self):
        if not self.well_coordinates:
            print("Error: No detected wells. Please run detection methods first.")
            return None
        
        img = self.image.copy()
        for well in self.well_coordinates:
            center_x, center_y = well["well_center"]
            radius = well["well_radius"]
            confidence = well["confidence"]

            ## Draw Circle and confidence
            cv2.circle(img, (center_x, center_y), 1, (0, 255, 0), 2)
            cv2.circle(img, (center_x, center_y), radius, (0, 255, 0), 2)

            # if confidence is not None:
            #     label = confidence # formatted 2 digits
            #     cv2.putText(img, label, (center_x, center_y - radius - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 0), 2)
        
        ## Check location of running
        # if "get_ipython" in globals():
        #     self.display_in_jupyter(img)
        # else:
        #     self.display_in_ide(img)

        self.check_jupyter_notebook(img)

    def check_jupyter_notebook(self, img):
        ## Reference: https://stackoverflow.com/questions/15411967/how-can-i-check-if-code-is-executed-in-the-ipython-notebook
        try:
            shell = get_ipython().__class__.__name__
            if shell == "ZMQInteractiveShell":
                self.display_in_jupyter(img)
            elif shell == "TerminalInteractiveShell":
                self.display_in_ide(img)
            else:
                self.display_in_ide
        except NameError:
            self.display_in_ide(img)

    def display_in_jupyter(self, img):
        plt.figure(figsize=(10,6))
        plt.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        plt.title(f"Detected Wells: {self.detected_method}")
        plt.axis('off')
        plt.show();
    
    def display_in_ide(self, img):
        cv2.imshow(f"Detected Wells: {self.detected_method}", img)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    @staticmethod
    def check_detect_dict(a_detect_dict):
        """
        {
        "well_center": (center_x, center_y),
        "well_radius": circle_radius,
        "confidence": f"{detect_conf:.2f}" # float or None
        }
        """
        detect_dict_keys = ["well_center", "well_radius", "confidence"]

        if not all(key in a_detect_dict for key in detect_dict_keys):
            return False
        if not isinstance(a_detect_dict["well_center"], tuple) and len(a_detect_dict["well_center"]) == 2:
            return False
        if not isinstance(a_detect_dict["well_radius"], int):
            return False
        if not (isinstance(a_detect_dict["confidence"], str) or (a_detect_dict["confidence"] == None)): # Either formatted string or None
            return False
        return True

    
    @staticmethod
    def check_detect_dict_list(detect_dict_list):
        """
        Apply this to all list of detect dicts
        """
        return all(WellDetector.check_detect_dict(a_dict) for a_dict in detect_dict_list)

# if __name__ =="__main__":

#     ref_img_path = "C:\\Users\\jleel\\Documents\\Project - Jira\\tempExtraction\\meltyfat\\data\\test_images\\test_plamatic_reference.jpeg"
#     detector = WellDetector(reference_img_path=ref_img_path)
#     # detector.load_image(reference_image_path=ref_img_path)

#     ## Hough Circles
#     hough_results = detector.detect_HoughCircles()
#     print(hough_results)

#     ## YOLO
#     yolo_results = detector.detect_YOLOv8(conf_threshold=0.8)
#     print(yolo_results)




    