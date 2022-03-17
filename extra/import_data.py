#!/usr/bin/env python3

import os
import re
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


def import_from_alissa(alissa_client, start_time, logger):
    '''Main function, for extracting the data from the Alissa output and send to function to parse to MongoDB'''
     # connection with MongoDB and the correct database "vus" and collection "lastUpdatedOn"
    mongo_client = pymongo.MongoClient(config.mongodb_localhost)
    db = mongo_client.vus.lastUpdatedOn
    
    # Retrieve the last time MongoDB has updated itself, to filter the latest Alissa analyses only
    last_updated_on_mongoDB = db.find_one({"version" : 1}, {"lastUpdatedOn":1, "_id":0})
    #If not exist yet, use '2018-01-01T00:00:00.000+0000' and add to mongo (first time use)
    if last_updated_on_mongoDB is None:
        db.replace_one({"version" : 1}, {"lastUpdatedOn" : '2018-01-01T00:00:00.000+0000', "version" : 1}, True)
        last_updated_on_mongoDB = db.find_one({"version" : 1}, {"lastUpdatedOn":1, "_id":0})
    
    last_updated_on_mongoDB = last_updated_on_mongoDB['lastUpdatedOn']
    
    # retrieving data from Alissa
    analysis = None
    for analysis in alissa_client.get_analyses(status='COMPLETED', 
                                        lastUpdatedAfter=last_updated_on_mongoDB, # format is '2020-01-01T00:00:00.000+0000'
                                        analysisPipelineName='ONB01',
                                        analysisType='INHERITANCE'): #add for testing [:x], where x is numer of iterations
        if analysis['classificationTreeName']:
            # retrieve basic info from Alissa about the analysis
            patient_dn_no = alissa_client.get_analysis_report(analysis['id'])[0]['reportName'].split("_")[0]
            logger.info('start Alissa retrieval of: %s' % patient_dn_no)
            inheritance_analysis = alissa_client.get_inheritance_analyses(analysis['id'])
            accession_number = alissa_client.get_patient(analysis['patientId'])['accessionNumber']
            export_id = alissa_client.post_inheritance_analyses_variants_export(analysis['id'], marked_review=True, marked_include_report=False)['exportId']
            analyis_sources = alissa_client.get_analysis_sources(analysis['id'])
            
            # retrieve the VUS/GUS info based on the analysis ID
            vus_export = None
            while vus_export is None:
                try:
                    time.sleep(5)  # 5 sec delay to request exported report.
                    vus_export = alissa_client.get_inheritance_analyses_variants_export(analysis['id'], export_id)
                except HTTPError as exception:
                    pass
            logger.info('Alissa retrieval completed of: %s' % patient_dn_no)
            # sometimes the there are no VUS marked or found within an analysis, then no info needs to be uploaded
            if vus_export == []:
                logger.info('Patient %s, has no VUS marked/found. Not uploaded to MongoDB' % patient_dn_no)
            else:
                upload_to_mongodb(inheritance_analysis, accession_number, analyis_sources, patient_dn_no, vus_export, logger)
    # if latest date does not retrieve any analyses from Alissa, quit program and try later
    if analysis is None:
        logger.info('no new analysis in Alissa since last upload to VUSualizer')
    # after uploading all analyses to MongoDB, replace time of last upload with starttime of script (before calling Alissa)
    db.replace_one({"version" : 1}, {"lastUpdatedOn" : start_time, "version" : 1}, True)


def upload_to_mongodb(inheritance_analysis, accession_number, analyis_sources, patient_dn_no, vus_export, logger):
    '''Function, for parsing data to the MongoDB'''
    # connection with MongoDB and the correct database "vus" and collection "variant"
    mongo_client = pymongo.MongoClient(config.mongodb_localhost)
    db = mongo_client.vus.variant
    
    # if DNnr already in mongoDB, check if updated an replace if neccesary
    last_updated_on_mongoDB = db.find_one({"dn_no" : patient_dn_no}, {"lastUpdatedOn":1, "_id":0})
    if last_updated_on_mongoDB:
        logger.info('dn_no: %s already present' % patient_dn_no)
        last_updated_on_mongoDB = last_updated_on_mongoDB['lastUpdatedOn']
        last_updated_on_Alissa = inheritance_analysis['lastUpdatedOn']
        if last_updated_on_Alissa == last_updated_on_mongoDB:
            logger.info('%s already in database, lastUpdatedOn Alissa is the same' % patient_dn_no) 
            return
        elif last_updated_on_Alissa > last_updated_on_mongoDB:
            db.delete_many({"dn_no": patient_dn_no})
            logger.info('removed: %s from database, start replacing with newer version' % patient_dn_no)
        elif last_updated_on_Alissa < last_updated_on_mongoDB:
            logger.info('lastUpdatedOn older than within the database for %s, this should not happen' % patient_dn_no)

    # get all relevant info from one patient into one dictionary.
    patient = {}
    patient["dn_no"] = patient_dn_no
    logger.info('start uploading to mongodb: %s' % patient_dn_no)
    patient["patient_accession_no"] = accession_number
    patient.update(inheritance_analysis)
    patient["analysis"] = patient.pop("reference")
    patient["platform_dataset"] = analyis_sources["platformDataSet"]["info"]

    # changes the format of the annotation sources from Alissa, to fit in MongoDB and resemble the old O-schijf format
    externalSources_dict = {}
    for source in analyis_sources['annotationSources']:
        source_name = ""
        source_value = ""
        for key, value in source.items():
            if key == 'name':
                source_name = value
            elif key == 'description':
                source_value = value
        if source_name and source_value:
            externalSources_dict[source_name] = source_value
        else:
            logger.info("error, externalsources has changed format in Alissa")
    patient["annotation_sources"] = externalSources_dict  # add previous section to total patient info
    
    # extract information from the VUS/variant data and add to "patient"
    for variant in vus_export:
        # format for gnomad Links. 4 availble in Alissa (snp, insertion, deletion and substitution)
        fullgnomen = variant['platformDatasets']['HGVS genomic-level nomenclature (fullGNomen)'] # NC_000001.10:g.123456789T>A
        variant['fullgnomen'] = fullgnomen
        if fullgnomen: # NC_000001.10:g.123456789T>A
            gnomad_data = re.split(':[a-z].', fullgnomen)[1] # 123456789T>A
            if variant["type"] == "snp":
                gnomad_data = [c for c in re.split(r'([-+]?\d*\.\d+|\d+)', gnomad_data) if c] # 123456789T>A
                gnomad_data = variant["chromosome"] + "-" + re.sub('[<>]+', '-',("-".join(gnomad_data))) # 1-123456789-T-A
                variant['GnomadVariant'] = {'Single nucleotide variant' : gnomad_data}
            elif variant["type"] == "insertion":
                gnomad_data = variant["chromosome"] + "-" + gnomad_data
                variant['GnomadVariant'] = {'Insertion' : gnomad_data}
                #TODO: make link format correctly for this genomic variation
            elif variant["type"] == "deletion":
                gnomad_data = variant["chromosome"] + "-" + gnomad_data
                variant['GnomadVariant'] = {'Deletion' : gnomad_data}
                #TODO: make link format correctly for this genomic variation
            elif variant["type"] == "substitution":
                gnomad_data = variant["chromosome"] + "-" + gnomad_data
                variant['GnomadVariant'] = {'Substitution' : gnomad_data}
                #TODO: make link format correctly for this genomic variation
        else: # on rare occasions, fullGNomen is empty
            variant['GnomadVariant'] = {variant["type"] : ''}
            
        # add VUS/variant info to patientdata
        variant.update(patient)
        db.insert_one(variant)
    logger.info('finished uploading to mongodb: %s' % patient_dn_no)


if __name__ == '__main__':
    # start_time of script functions
    start_time = datetime.now(timezone.utc).isoformat()
    
    # Create Alissa connection based on config.py (fill details there)
    alissa_client = AlissaInterpret(
        base_uri=config.alissa_base_uri, client_id=config.alissa_client_id, client_secret=config.alissa_client_secret,
        username=config.alissa_username, password=config.alissa_password
    )

    # configuration for the logging file. This file logs the import of excel files into MongoDB and errors
    with open(config.logging_file, 'r') as configfile:
        logging.config.dictConfig(yaml.safe_load(configfile))
    logger = logging.getLogger(__name__)
    logger.info("File upload script 'import_data.py' started")

    # Start importing from Alissa and exporting to MongoDB
    import_from_alissa(alissa_client, start_time, logger)

    # end_time of script and printing total processing time
    end_time = datetime.now(timezone.utc).isoformat()
    diff = (dateutil.parser.isoparse(start_time) - dateutil.parser.isoparse(end_time))
    print("## \t\tFinished in %.2f minutes" % (diff.total_seconds()/60))
