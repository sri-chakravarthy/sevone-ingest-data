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

         
        # Exit with 0 for container to not restart    
        sys.exit(0)


            
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"An unexpected error occurred: {tb}")
        #Exit container without restart
        sys.exit(0)




