from setuptools import setup, find_packages

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="meltyfat", # package name
    version="0.0.1",
    description="A proof-of-concept Python module for detection and extraction of HIKMICRO Pocket 2 radiometric thermography image on 96-well plate for a high-throughput studies of material thermal properties.",
    description_content_type="text/markdown; charset=UTF-8; variant=GFM",
    long_description=long_description,
    long_description_content_type="text/markdown; charset=UTF-8; variant=GFM",
    url="https://github.com/JiraLeelas/meltyfat",
    author="Jira Leelasoontornwatana",
    author_email="jira.leelas@gmail.com",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
    ],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "torch",
        "numpy",
        "pandas",
        "ultralytics",
        "opencv-python",
        "matplotlib"
    ],
    python_requires=">=3.11",
)