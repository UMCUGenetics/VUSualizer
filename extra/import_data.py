#!/usr/bin/env python3

import os
import time
import pymongo
import logging
import logging.config
import yaml
import config
from requests.exceptions import HTTPError
from alissa_interpret_client.alissa_interpret import AlissaInterpret

# Create Alissa connection based on config.py (fill details there)
client = AlissaInterpret(
    base_uri=config.alissa_base_uri, client_id=config.alissa_client_id, client_secret=config.alissa_client_secret,
    username=config.alissa_username, password=config.alissa_password
)

# configuration for the logging file. This file logs the import of excel files into MongoDB and errors
with open("./logging_config.yml", 'r') as configfile:
    logging.config.dictConfig(yaml.safe_load(configfile))

logger = logging.getLogger(__name__)
logger.debug("File upload script 'import_data.py' started")
start_time = time.time()

def main():
    '''Main function, for extracting the data from the Alissa output and send to function to parse to MongoDB'''
    for analysis in client.get_analyses(status='COMPLETED', 
                                        created_after='2021-01-01T00:00:00.000+0000', 
                                        analysisPipelineName='ONB01',
                                        analysisType='INHERITANCE')[:1]: #remove [:x] if all
        if not analysis['classificationTreeName']:  # Skip analysis
            continue
        else:
            patient_dn_no = client.get_report(analysis['id'])[0]['reportName'].split("_")[0]
            logger.debug('start Alissa retrieval of: %s' % patient_dn_no)
            ONB01_analysis = client.get_inheritance_analyses(analysis['id'])
            accession_number = client.get_patient(analysis['patientId'])['accessionNumber']
            export_id = client.post_inheritance_analyses_variants_export(analysis['id'], marked_review=True, marked_include_report=False)['exportId']
            analyis_sources = client.get_sources(analysis['id'])
            
            
            VUS_response = None
            while VUS_response is None:
                try:
                    time.sleep(5)  # 5 sec delay to request exported report.
                    VUS_response = client.get_inheritance_analyses_variants_export(analysis['id'], export_id)
                    #response.raise_for_status()
                except HTTPError as exception:
                    print(exception)
                    pass
            logger.debug('Alissa retrieval completed of: %s' % patient_dn_no)
            upload_to_mongodb(ONB01_analysis, accession_number, analyis_sources, patient_dn_no, VUS_response)

def upload_to_mongodb(ONB01_analysis, accession_number, analyis_sources, patient_dn_no, VUS_response):
    '''Function, for parsing data to the MongoDB'''
    # connection with MongoDB and the correct collection "vus"
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client.vus.variant

    patient = {}
    patient["dn_no"] = patient_dn_no
    logger.debug('start uploading to mongodb: %s' % patient_dn_no)
    
    patient["patient_accession_no"] = accession_number
    patient.update(ONB01_analysis)
    patient["analysis"] = patient.pop("reference")
    patient["platform_dataset"] = analyis_sources["platformDataSet"]["info"]

    # changes the format of the annotation sources from Alissa, to fit in MongoDB and resemble the old O-schijf format
    externalSources_dict = {}
    variants = VUS_response
    for key in analyis_sources['annotationSources']:
        source_name = ""
        source_value = ""
        for x,y in key.items():
            if x == 'name':
                source_name = y
            elif x == 'description':
                source_value = y
            else:
                continue
        if source_name != "" and source_value != "":
            externalSources_dict[source_name] = source_value
        else:
            print("error, externalsources has changed format in Alissa")
    patient["annotation_sources"] = externalSources_dict  # add previous section to total patient info
    
    # add VUS info to patientdata
    for item in variants:
            variant = item
            variant.update(patient)
            db.insert_one(variant)

    logger.debug('finished uploading to mongodb: %s' % patient_dn_no)
    print("## \t\tFinished in {0:.2f} minutes".format((time.time() - start_time) / 60))

if __name__ == '__main__':
    main()
