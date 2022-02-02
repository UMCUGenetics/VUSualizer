#!/usr/bin/env python3

import os
import time
import sys
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
logger.info("File upload script 'import_data.py' started")
start_time = time.time()

def main():
    '''Main function, for extracting the data from the Alissa output and send to function to parse to MongoDB'''
    for analysis in client.get_analyses(status='COMPLETED', 
                                        created_after='2021-01-01T00:00:00.000+0000', 
                                        analysisPipelineName='ONB01',
                                        analysisType='INHERITANCE'): #add [:x] for testing x times
        if not analysis['classificationTreeName']:  # Skip analysis
            continue
        else:
            patient_dn_no = client.get_report(analysis['id'])[0]['reportName'].split("_")[0]
            logger.info('start Alissa retrieval of: %s' % patient_dn_no)
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
            logger.info('Alissa retrieval completed of: %s' % patient_dn_no)
            # sometimes the there are no VUS marked or found, then no info needs to be uploaded
            if VUS_response == []:
                logger.info('Patient %s, has no VUS marked/found. Not uploaded to MongoDB' % patient_dn_no)
                continue
            else:
                upload_to_mongodb(ONB01_analysis, accession_number, analyis_sources, patient_dn_no, VUS_response)

def upload_to_mongodb(ONB01_analysis, accession_number, analyis_sources, patient_dn_no, VUS_response):
    '''Function, for parsing data to the MongoDB'''
    # connection with MongoDB and the correct collection "vus"
    client = pymongo.MongoClient("mongodb://localhost:27017/")
    db = client.vus.variant
    
    # if DNnr already in mongoDB, check if updated an replace if neccesary
    if db.count_documents({"dn_no": patient_dn_no}) > 0:
        logger.info('dn_no: %s already present' % patient_dn_no)
        # get and parse "lastUpdatedOn" from MongoDB/Alissa for specific patient_dn_no
        lastUpdatedOn_mongoDB = db.find_one({"dn_no" : patient_dn_no}, {"lastUpdatedOn":1, "_id":0})
        for key, value in lastUpdatedOn_mongoDB.items():
            lastUpdatedOn_mongoDB = value
        lastUpdatedOn_Alissa = ONB01_analysis['lastUpdatedOn']
        if lastUpdatedOn_Alissa == lastUpdatedOn_mongoDB:
            logger.info('%s already in database, lastUpdatedOn Alissa is the same' % patient_dn_no) 
            return
        elif lastUpdatedOn_Alissa > lastUpdatedOn_mongoDB:
            db.delete_many({"dn_no": patient_dn_no})
            logger.info('removed: %s from database, start replacing with newer version' % patient_dn_no)
        elif lastUpdatedOn_Alissa < lastUpdatedOn_mongoDB:
            logger.info('lastUpdatedOn older than within the database for %s, this should not happen' % patient_dn_no)
            sys.exit('lastUpdatedOn older than within the database for %s, this should not happen' % patient_dn_no)
        else:
            logger.info('unknown error lastUpdatedOn for patient %s, this should not happen' % patient_dn_no)
            sys.exit('unknown error lastUpdatedOn for patient %s, this should not happen' % patient_dn_no)

    patient = {}
    patient["dn_no"] = patient_dn_no
    logger.info('start uploading to mongodb: %s' % patient_dn_no)
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
    logger.info('finished uploading to mongodb: %s' % patient_dn_no)


if __name__ == '__main__':
    main()
    print("## \t\tFinished in {0:.2f} minutes".format((time.time() - start_time) / 60))