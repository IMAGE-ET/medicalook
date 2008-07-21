CREATE TYPE sex AS ENUM ('m', 'f', '');
CREATE TABLE images (
    id bigserial primary key,
    patient_name character varying (255) NOT NULL default '',
    patient_sex sex,
    patient_dob date NOT NULL default (date '1900-01-01'),
    body_part character varying (255) NOT NULL default '',
    description text NOT NULL default '',
    modality character varying (255) NOT NULL default '',
    study_date date NOT NULL default (date '1900-01-01'),
    station character varying (255) NOT NULL default '',
    created timestamp NOT NULL default current_timestamp,
    filename character (40) NOT NULL default ''
);