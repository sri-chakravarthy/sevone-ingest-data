import requests
from logger_config import logger
from PasswordEncryption import *
import traceback
import os
import os.path
import base64
import time
import sys
from SevOneAppliance import *
import threading
from concurrent.futures import ThreadPoolExecutor
import fcntl 
import shutil
from concurrent.futures import as_completed

def transform_device_data(input_data):
    #logger.info(f"Parsing and Ingesting: {input_data}")
    dev_ob_ind_list = []
    deviceObjectDict = {}
    objectList = []
    for objectDetails in input_data:
        logger.debug(f'Checking device : {objectDetails["deviceName"]}, Object: {objectDetails["objectName"]}')
        if objectDetails["deviceName"] not in deviceObjectDict:
            deviceObjectDict[objectDetails["deviceName"]] = []
        indicatorList = []
        #logger.debug(f'Indicators to be process : {objectDetails["measResults"]}')
        for indicatorDetails in objectDetails["measResults"]:
            #logger.debug(f'Checking Indicator : {indicatorDetails}')
            indicatorDict = {
                "format": indicatorDetails["indicatorFormat"].split('.')[-1],
                "name": indicatorDetails["indicatorName"],
                "units": indicatorDetails["indicatorUnit"],
                "value": indicatorDetails["indicatorValue"],
            }
            indicatorList.append(indicatorDict)
        #logger.debug(f'Checking IndicatorLost : {indicatorList}')
        objectDict = {
            "automaticCreation": True,
            "description": objectDetails["objectName"],
            "name": objectDetails["objectName"],
            "pluginName": "DEFERRED",
            "timestamps": [
                {
                "indicators": indicatorList,
                "timestamp": objectDetails["granPeriodEndTime"]
                }
            ],
            "type": objectDetails["objectType"]
        }
        deviceObjectDict[objectDetails["deviceName"]].append(objectDict)
    for device, objDetails in deviceObjectDict.items():
        dev_ob_ind_list.append({"automaticCreation": True,
            "distributionOnAllPeers": True,
            "name": device,
            "ip" : "",
            "objects":objDetails })
    logger.debug(f"DeviceObjectDict To ingest: {dev_ob_ind_list}")
    return dev_ob_ind_list
    

def chunk_list(data_list, chunk_size):
    for i in range(0, len(data_list), chunk_size):
        yield data_list[i:i + chunk_size]

def process_file(file_path,archive_dir,SevOne_appliance_obj):
    try:
        with open(file_path, 'r') as f:
            #fcntl.flock(f, fcntl.LOCK_EX)
            json_data = json.load(f)
            #fcntl.flock(f, fcntl.LOCK_UN)

        transformed_data = transform_device_data(json_data)

        if isinstance(transformed_data, list):
            for d in transformed_data:
                SevOne_appliance_obj.ingest_dev_obj_ind(
                    d.get("name", ""),
                    d.get("ip", ""),
                    d.get("objects", [])
                )
        else:
            logger.error(f"Unexpected transformed data: {transformed_data}")

        os.makedirs(archive_dir, exist_ok=True)
        shutil.move(file_path, os.path.join(archive_dir, os.path.basename(file_path)))

    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")

def process_file_batch(file_batch, archive_dir, SevOne_appliance_obj):
    """Process a list of files (a batch) sequentially in a thread"""
    for file_path in file_batch:
        logger.info(f"[Thread] Processing file: {file_path}")
        process_file(file_path, archive_dir, SevOne_appliance_obj)

# Main function to scan the folder and process files with threads
def process_folder_multithreaded(SevOne_appliance_obj, folder_path, archive_dir, batch_size=100, max_threads=16):
    json_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.json')]
    logger.info(f"Found {len(json_files)} files")

    #file_batches = list(chunk_list(json_files, batch_size))
    futures = []
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        
        
        # Submit process_file, which itself submits more tasks
        #logger.info(f"Processing file: {file}")
        future_to_file = {executor.submit(process_file, file, archive_dir, SevOne_appliance_obj): file for file in json_files}
        for future in as_completed(future_to_file):
            file = future_to_file[future]
            try:
                result = future.result()
                logger.info(f"Ingested {file} successfully.")
            except Exception as e:
                logger.debug(f"Error processing {file}: {e}")

        '''
        for batch in file_batches:
            future = executor.submit(process_file_batch, batch, archive_dir, SevOne_appliance_obj)
            futures.append(future)
       

        # Wait for all batches to finish
        for future in as_completed(futures):
            try:
                future.result()  # This raises any exceptions if occurred
            except Exception as e:
                logger.error(f"Batch failed with error: {e}")
         '''
if __name__ == '__main__':
    try:

        logger.info('-----------------------------------------------------------------------------------------------------------');
        logger.info('Starting execution of application')
        loop_start = int(time.time())

        
        file_prefix = ""
        #configurationFile = "/opt/IBM/expert-labs/el-proj-templates/etc/config.json"
        #keyFile = "/opt/IBM/expert-labs/el-proj-templates/env/key.txt"
        configurationFile = file_prefix + "etc/config.json"
        keyFile = file_prefix + "env/key.txt"
        with open(keyFile,"r") as keyfile:
            key=keyfile.read()
        EncryptConfigurationFile(configurationFile,keyFile,"ApplianceDetails","List")
        with open(configurationFile, "r") as f:
            try:
                config = json.load(f)
            except json.decoder.JSONDecodeError as e:
                logger.error(f"Error loading JSON data: {e}")
                loop_finish = time.time()                
                

        logger.info(config)


            
        #Ingesting the metrics into SevOne Appliance
        
        ###### Check Master-Slave situation ######
        
        logger.info(f"Checking if host is PAS/HSA")
        
        
        '''
        with open(f'{file_prefix}SevOne.masterslave.master') as f:
            if f.read().rstrip() == '0':
            
                logger.critical('loop:' + str(loop_count) + ' Running on Secondary appliance ... Skipping loop increase...')
                loop_finish = time.time()
                # go to sleep till next poll
                
                if go_to_sleep(loop_start, loop_finish,loop_count,config["interval"]):
                    continue
                else:
                    break
        '''
        
        logger.info(f"Host is PAS. Continuing...")
       
        keyFile = file_prefix + "env/key.txt"
        with open(keyFile,"r") as keyfile:
            key=keyfile.read()
        SevOne_appliance_obj = SevOneAppliance(config["ApplianceDetails"][0]["IPAddress"],config["ApplianceDetails"][0]["UserName"],DecryptPassword(config["ApplianceDetails"][0]["Password"]["EncryptedPwd"].encode('utf-8'),key),config["ApplianceDetails"][0]["sshUserName"],DecryptPassword(config["ApplianceDetails"][0]["sshPassword"]["EncryptedPwd"].encode('utf-8'),key),config["ApplianceDetails"][0]["UseSShKeys"])

        #Create an objectList to be ingested

        timestamp = int(time.time())
        process_folder_multithreaded(SevOne_appliance_obj,config["FilePath"],config["ArchivedDir"],config["BatchSize"],config["MaxThreads"])
        
        '''
        objectList = []

        #Create an Object Dictionary - One dict per object with all indicators in that object.
        objectDict = {
                "automaticCreation": True,
                "description": "Group members Count Metrics",
                "name": ShortDevGroupPath,
                "pluginName": "DEFERRED",
                "timestamps": [
                    {
                    "indicators": [
                        {
                        "format": "GAUGE",
                        "name": "<indicatorName",
                        "units": "<unit>",
                        "value": <indicatorValue>
                        }
                    ],
                    "timestamp": timestamp
                    }
                ],
                "type": <ObjectTypeName>
            }
             
            # Append the dictionary to the objectList
            if objectDict["name"] != "":
                objectList.append(objectDict)
        

        logger.info(f"ObjectList: {json.dumps(objectList, indent=4)}")
        result = SevOne_appliance_obj.ingest_dev_obj_ind(automationDict["Name"],automationDict["IPToBeCreated"],objectList)'
        '''
        '''
        dev_ob_ind_list = [
        {
            "automaticCreation": True,
            "distributionOnAllPeers": True,
            "name": "test1",
            "ip": "100.1.1.1",
            "objects":
            [{
                "automaticCreation": True,
                "description": "Group members Count Metrics",
                "name": "testObject1",
                "pluginName": "DEFERRED",
                "timestamps": [
                    {
                    "indicators": [
                        {
                        "format": "GAUGE",
                        "name": "No of Stations",
                        "units": "Number",
                        "value": "1"
                        }
                    ],
                    "timestamp": timestamp
                    }
                ],
                    "type": "Device Group Counts"
            },
            {
                "automaticCreation": True,
                "description": "Group members Count Metrics",
                "name": "testObject2",
                "pluginName": "DEFERRED",
                "timestamps": [
                    {
                    "indicators": [
                        {
                        "format": "GAUGE",
                        "name": "No of Stations",
                        "units": "Number",
                        "value": "2"
                        }
                    ],
                    "timestamp": timestamp
                    }
                ],
                    "type": "Device Group Counts"
            }]
        },
        {
            "automaticCreation": True,
            "distributionOnAllPeers": True,
            "name": "test2",
            "ip": "100.1.1.3",
            "objects":
            [{
                "automaticCreation": True,
                "description": "Group members Count Metrics",
                "name": "testObject3",
                "pluginName": "DEFERRED",
                "timestamps": [
                    {
                    "indicators": [
                        {
                        "format": "GAUGE",
                        "name": "No of Stations",
                        "units": "Number",
                        "value": "3"
                        }
                    ],
                    "timestamp": timestamp
                    }
                ],
                    "type": "Device Group Counts"
            },
            {
                "automaticCreation": True,
                "description": "Group members Count Metrics",
                "name": "testObject4",
                "pluginName": "DEFERRED",
                "timestamps": [
                    {
                    "indicators": [
                        {
                        "format": "GAUGE",
                        "name": "No of Stations",
                        "units": "Number",
                        "value": "5"
                        }
                    ],
                    "timestamp": timestamp
                    }
                ],
                    "type": "Device Group Counts"
            }]
        }
        ]
        SevOne_appliance_obj.ingest_multi_dev_obj_ind(dev_ob_ind_list)
        '''

        # Exit with 0 for container to not restart    
        sys.exit(0)


            
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"An unexpected error occurred: {tb}")
        #Exit container without restart
        sys.exit(0)




