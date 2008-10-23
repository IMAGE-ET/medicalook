#!/usr/bin/env python
#
# import_thread.py: a thread for importing a new file
# author: Wu Zhe <jessewoo at gmail.com>
# license: GPL

import os

import common
import db
from dicomparser import DicomParser


def parse_file(filename):
    path = os.path.join(common.file_dir, filename)
    parser = DicomParser()
    parser.set_file(path)
    parser.parse()
    data = parser.get_data()
    data['filename'] = filename
    return data

def get_id(res):
    print "here should return an id"

def insert_data(data):
    d = db.run_op("""INSERT INTO images
    (patient_name, patient_sex, patient_dob,
    body_part, description, modality, study_date,
    station, filename)
    VALUES
    ('%(patient_name)s', '%(patient_sex)s', DATE '%(patient_dob)s',
    '%(body_part)s', '%(description)s', '%(modality)s',
    DATE '%(study_date)s', '%(station)s', '%(filename)s')""" % data)
    d.addCallback(get_id)
