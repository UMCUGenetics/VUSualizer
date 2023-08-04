#!/data/vusualizer/venv/bin/python3

import re
import time
import pymongo
import logging
import json
import logging.config
import yaml
import config
import dateutil.parser
from requests.exceptions import HTTPError
from alissa_interpret_client.alissa_interpret import AlissaInterpret
from datetime import datetime, timezone


def import_from_alissa(alissa_client, start_time, logger):
    '''Main function, for extracting the data from the Alissa output and send to function to parse to MongoDB'''

    # connection with MongoDB and the correct database 'vus' and collection 'lastUpdatedOn'
    mongo_client = pymongo.MongoClient(config.mongodb_localhost)
    db = mongo_client.vus.lastUpdatedOn

    # Retrieve the last time MongoDB has updated itself, to filter the latest Alissa analyses only
    last_updated_on_mongoDB = db.find_one({'version': 1}, {'lastUpdatedOn': 1, '_id': 0})
    # If not exist yet, use '2018-01-01T00:00:00.000+0000' and add to mongo (first time use)
    if last_updated_on_mongoDB is None:
        db.replace_one({'version': 1}, {'lastUpdatedOn': '2018-01-01T00:00:00.000+0000', 'version': 1}, True)
        last_updated_on_mongoDB = db.find_one({'version': 1}, {'lastUpdatedOn': 1, '_id': 0})

    last_updated_on_mongoDB = last_updated_on_mongoDB['lastUpdatedOn']

    # retrieving data from Alissa
    analysis = None
    for analysis in alissa_client.get_analyses(
        status='COMPLETED',
        lastUpdatedAfter=last_updated_on_mongoDB,  # '2020-01-01T00:00:00.000+0000'
        analysisPipelineName='ONB01',
        analysisType='INHERITANCE'
    ):

        if analysis['classificationTreeName']:
            logger.info(f"Start Alissa retrieval of: {analysis['reference']} with analysisID: {analysis['id']}")

            # retrieve basic info from Alissa about the analysis
            inheritance_analysis = alissa_client.get_inheritance_analyses(analysis['id'])
            accession_number = alissa_client.get_patient(analysis['patientId'])['accessionNumber']
            analyis_sources = alissa_client.get_analysis_sources(analysis['id'])

            # retrieve the VUS/GUS info based on the analysis ID
            export_id = alissa_client.post_inheritance_analyses_variants_export(
                analysis['id'],
                marked_review=True,
                marked_include_report=False
            )['exportId']
            vus_export = None
            while vus_export is None:
                try:
                    time.sleep(5)  # 5 sec delay to request exported report.
                    vus_export = alissa_client.get_inheritance_analyses_variants_export(analysis['id'], export_id)
                except HTTPError:
                    pass
                except json.decoder.JSONDecodeError:
                    break
            logger.info(f"Alissa retrieval completed of: {analysis['reference']}")

            if vus_export is None:
                logger.error(f"Analysis {analysis['reference']} not uploaded, Alissa database temporarily not available")
                # TODO send (email) notification of this error
                exit(1)
            else:
                # Make analysis_reference compatible with webtool uri and upload to mongoDB
                analysis_reference = re.sub(" |/", '_', analysis['reference'])  # replace space and / with _
                upload_to_mongodb(
                    inheritance_analysis,
                    accession_number,
                    analyis_sources,
                    analysis_reference,
                    vus_export,
                    logger,
                )

    # if latest date does not retrieve any analyses from Alissa, quit program and try later
    if analysis is None:
        logger.info("No new analysis in Alissa since last upload to VUSualizer")
    # after uploading all analyses to MongoDB, replace time of last upload with starttime of script (before calling Alissa)
    db.replace_one({'version': 1}, {'lastUpdatedOn': start_time, 'version': 1}, True)


def upload_to_mongodb(inheritance_analysis, accession_number, analyis_sources, analysis_reference, vus_export, logger):
    '''Function, for parsing data to the MongoDB'''

    # connection with MongoDB and the correct database "vus" and collection "variant"
    mongo_client = pymongo.MongoClient(config.mongodb_localhost)
    db = mongo_client.vus.variant

    # if analysis_reference already in mongoDB, check if updated and replace if neccesary
    last_updated_on_mongoDB = db.find_one({'analysis_reference': analysis_reference}, {'lastUpdatedOn': 1, '_id': 0})
    if last_updated_on_mongoDB:
        logger.info(f"analysis_reference: {analysis_reference} already present")
        last_updated_on_mongoDB = last_updated_on_mongoDB['lastUpdatedOn']
        last_updated_on_Alissa = inheritance_analysis['lastUpdatedOn']
        if last_updated_on_Alissa == last_updated_on_mongoDB:
            logger.info(f"{analysis_reference} already in database, lastUpdatedOn Alissa is the same")
            return
        elif last_updated_on_Alissa > last_updated_on_mongoDB:
            db.delete_many({"analysis_reference": analysis_reference})
            logger.info(f"Removed: {analysis_reference} from database, start replacing with newer version")
        elif last_updated_on_Alissa < last_updated_on_mongoDB:
            logger.error(f"lastUpdatedOn older than within the database for {analysis_reference}, this should not happen")
            # TODO send (email) notification of this error

    # get all relevant info from one patient into one dictionary.
    patient = {}
    patient['analysis_reference'] = analysis_reference
    logger.info('Start uploading to mongodb: %s' % analysis_reference)
    patient['patient_accession_no'] = accession_number
    patient.update(inheritance_analysis)
    patient['analysis'] = patient.pop('reference')
    patient['platform_dataset'] = analyis_sources['platformDataSet']['info']

    # changes the format of the annotation sources from Alissa, to fit in MongoDB and resemble the old O-schijf format
    externalSources_dict = {}
    for source in analyis_sources['annotationSources']:
        source_name = ''
        source_value = ''
        for key, value in source.items():
            if key == 'name':
                source_name = value
            elif key == 'description':
                source_value = value
        if source_name and source_value:
            externalSources_dict[source_name] = source_value
        else:
            logger.error("Error, the parameter 'externalSources' has changed format in Alissa")
    patient['annotation_sources'] = externalSources_dict  # add previous section to total patient info

    # extract information from the VUS/variant data and add to 'patient'
    # Set default tot prevent empty field
    patient['vus_is_empty'] = False
    if not vus_export:
        # If there is no VUS found for this analysis / patient, upload only the patient data in the database
        logger.info(f"Analysis {patient['analysis_reference']}, has no VUS marked/found. Upload empty VUS warning to MongoDB")
        patient['vus_is_empty'] = True
        db.insert_one(patient)

    for variant in vus_export:
        # format for gnomad Links. 4 availble in Alissa (snp, insertion, deletion and substitution)
        try:
            fullgnomen = variant['platformDatasets']['HGVS genomic-level nomenclature (fullGNomen)']
            variant['fullgnomen'] = fullgnomen  # NC_000001.10:g.12345678T>A
        except (KeyError, TypeError):
            logger.error(
                f"Variant in patient {analysis_reference} has no platformDatasets and fullGNomen, variant not uploaded"
            )
            continue
        if fullgnomen:  # NC_000001.10:g.12345678T>A
            gnomad_id = fullgnomen.split(':g.')[1]  # 123456789T>A
            if variant['type'] == 'snp':
                gnomad_id = re.match('(?P<pos>\d+)(?P<ref>[A-Z])>(?P<alt>[A-Z])', gnomad_id, re.IGNORECASE).groupdict()  # {'pos': '12345678', 'ref': 'T', 'alt': 'A'}
                gnomad_id = f"{variant['chromosome']}-{gnomad_id['pos']}-{gnomad_id['ref']}-{gnomad_id['alt']}"
                variant['GnomadVariant'] = {'Single nucleotide variant': gnomad_id}
            elif variant['type'] in ['insertion', 'deletion', 'substitution']:
                gnomad_id = gnomad_id = f"{variant['chromosome']}-{gnomad_id}"
                variant['GnomadVariant'] = {variant['type'].capitalize(): gnomad_id}
                # TODO: make link format correctly for 'insertion', 'deletion', 'substitution' genomic variations
        else:  # on rare occasions, fullGNomen is empty
            variant['GnomadVariant'] = {variant['type']: ''}

        # Remove . form externalDatabases keys
        external_databases = variant['externalDatabases']
        external_databases = {key.replace('.', '_'): value for key, value in external_databases.items()}
        variant['externalDatabases'] = external_databases

        # add VUS/variant info to patientdata
        variant.update(patient)
        db.insert_one(variant)
    logger.info('Finished uploading to mongodb: %s' % analysis_reference)


if __name__ == '__main__':
    # start_time of script functions
    start_time = datetime.now(timezone.utc).isoformat()

    # Create Alissa connection based on config.py (fill details there)
    alissa_client = AlissaInterpret(
        base_uri=config.alissa_base_uri, client_id=config.alissa_client_id, client_secret=config.alissa_client_secret,
        username=config.alissa_username, password=config.alissa_password
    )

    # configuration for the logging file.
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
