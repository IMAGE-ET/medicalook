#!/usr/bin/env python
#
# dicomparser.py: parse data from dicom files
# author: Wu Zhe <jessewoo at gmail.com>
# license: GPL


import metadata

class DicomParser:
    def __init__(self):
        pass

    def set_file(self, path):
        self.dicom_file = path

    def parse(self):
        from InsightToolkit import itkImageFileReaderUS2_New, \
             itkGDCMImageIO_New

        reader = itkImageFileReaderUS2_New()
        dicom_io = itkGDCMImageIO_New()
        reader.SetImageIO(dicom_io.GetPointer())
        reader.SetFileName(self.dicom_file)
        reader.Update()

        data_pair = {'patient_name': dicom_io.GetPatientName,
                     'patient_sex':dicom_io.GetPatientSex,
                     'patient_dob': dicom_io.GetPatientDOB,
                     'body_part': dicom_io.GetBodyPart,
                     'description': dicom_io.GetStudyDescription,
                     'modality': dicom_io.GetModality,
                     'study_date': dicom_io.GetStudyDate,
                     'station': dicom_io.GetManufacturer
                     }

        data = dict()
        for name in data_pair.keys():
            st = ' ' * 255
            data_pair[name](st)
            st = st.strip()
            if st.endswith('\x00'):
                st = st[:-1]
            data[name] = st.strip()

        # validate sex
        sex = data['patient_sex']
        if sex.lower().startswith('m'):
            data['patient_sex'] = 'm'
        elif sex.lower().startswith('f'):
            data['patient_sex'] = 'f'
        else:
            data['patient_sex'] = ''

        def get_date(raw):
            if len(raw) == 8:
                date = raw.replace('.', '')
            else:
                date = '1900-01-01'
            return date

        data['patient_dob'] = get_date(data['patient_dob'])
        data['study_date'] = get_date(data['study_date'])
        self.data = data

    def get_data(self):
        return self.data
