#!/usr/bin/env python3

import os
import time
import sys
import pymongo
import logging
import logging.config
import yaml
import config
import dateutil.parser
from requests.exceptions import HTTPError
from alissa_interpret_client.alissa_interpret import AlissaInterpret
from datetime import datetime, timezone

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

# start_time of script functions
start_time = datetime.now(timezone.utc).isoformat()


def main():
    '''Main function, for extracting the data from the Alissa output and send to function to parse to MongoDB'''
     # connection with MongoDB and the correct database "vus" and collection "lastUpdatedOn"
    mongoclient = pymongo.MongoClient("mongodb://localhost:27017/")
    db = mongoclient.vus.lastUpdatedOn
    
    # Retrieve the last time MongoDB has updated itself, to filter the latest Alissa analyses only
    lastUpdatedOn_mongoDB = db.find_one({"version" : 1}, {"lastUpdatedOn":1, "_id":0})
    #If not exist yet, use '2018-01-01T00:00:00.000+0000' and add to mongo (first time use)
    if lastUpdatedOn_mongoDB is None:
        db.replace_one({"version" : 1}, {"lastUpdatedOn" : '2018-01-01T00:00:00.000+0000', "version" : 1}, True)
        lastUpdatedOn_mongoDB = db.find_one({"version" : 1}, {"lastUpdatedOn":1, "_id":0})
    
    for key, value in lastUpdatedOn_mongoDB.items():
        lastUpdatedOn_mongoDB = value
    
    # retrieving data from Alissa
    analysis = None
    for analysis in client.get_analyses(status='COMPLETED', 
                                        lastUpdatedAfter=lastUpdatedOn_mongoDB, # format is '2020-01-01T00:00:00.000+0000'
                                        analysisPipelineName='ONB01',
                                        analysisType='INHERITANCE'): #add for testing [:x], where x is numer of iterations
        if not analysis['classificationTreeName']:  # Skip analysis
            continue
        else:
            # retrieve basic info from Alissa about the analysis
            patient_dn_no = client.get_report(analysis['id'])[0]['reportName'].split("_")[0]
            logger.info('start Alissa retrieval of: %s' % patient_dn_no)
            ONB01_analysis = client.get_inheritance_analyses(analysis['id'])
            accession_number = client.get_patient(analysis['patientId'])['accessionNumber']
            export_id = client.post_inheritance_analyses_variants_export(analysis['id'], marked_review=True, marked_include_report=False)['exportId']
            analyis_sources = client.get_sources(analysis['id'])
            
            # retrieve the VUS/GUS info based on the analysis ID
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
            # sometimes the there are no VUS marked or found within an analysis, then no info needs to be uploaded
            if VUS_response == []:
                logger.info('Patient %s, has no VUS marked/found. Not uploaded to MongoDB' % patient_dn_no)
                continue
            else:
                upload_to_mongodb(ONB01_analysis, accession_number, analyis_sources, patient_dn_no, VUS_response)
    # if latest date does not retrieve any analyses from Alissa, quit program and try later
    if analysis is None:
        logger.info('no new analysis in Alissa since last upload to VUSualizer')
        sys.exit(0)
    # after uploading all analyses to MongoDB, replace time of last upload with starttime of script (before calling Alissa)
    db.replace_one({"version" : 1}, {"lastUpdatedOn" : start_time, "version" : 1}, True)


def upload_to_mongodb(ONB01_analysis, accession_number, analyis_sources, patient_dn_no, VUS_response):
    '''Function, for parsing data to the MongoDB'''
    # connection with MongoDB and the correct database "vus" and collection "variant"
    mongoclient = pymongo.MongoClient("mongodb://localhost:27017/")
    db = mongoclient.vus.variant
    
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

    # get all relevant info from one patient into one dictionary.
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
    end_time = datetime.now(timezone.utc).isoformat()
    diff = (dateutil.parser.isoparse(start_time) - dateutil.parser.isoparse(end_time))
    print("## \t\tFinished in %.2f minutes" % (diff.total_seconds()/60))
