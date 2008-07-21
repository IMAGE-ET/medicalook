#!/usr/bin/env python
#
# metadata.py: define data structure
# author: Wu Zhe <jessewoo at gmail.com>
# license: GPL


headers = ["ID", "Patient name", "Sex",  "DOB", "Body part", "Description",
           "Modality", "Study date", "Station", "Import time", "File name"]
columns = ["id", "patient_name", "patient_sex",  "patient_dob", "body_part", "description",
           "modality", "study_date", "station", "created", "filename"]

connector = {"id": "=",
             "patient_name": "~*",
             "patient_sex": "=",
             "patient_dob": "=",
             "body_part": "~*",
             "description": "~*",
             "modality": "=",
             "study_date": "=",
             "station": "~*",
             "created": "=",
             "filename": "~*"}

