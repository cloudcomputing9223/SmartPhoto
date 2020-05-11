import json
import boto3
import os
import sys
import uuid
from botocore.vendored import requests
from datetime import *
import urllib3

http = urllib3.PoolManager()
          
REGION = 'us-east-1'
ES_HOST = 'https://vpc-photos-em6q2gg7sstox7upwcuobtl7ym.us-east-1.es.amazonaws.com'
ES_ENDPOINT = 'https://vpc-photos-em6q2gg7sstox7upwcuobtl7ym.us-east-1.es.amazonaws.com'
ES_INDEX = 'photos'
ES_TYPE = 'Photo'

def lambda_handler(event, context):
    print('INPUT EVENT DATA:')
    print(event)
    
    cors = {
        "Access-Control-Allow-Origin": "*",
        'Content-Type': 'application/json'
    }

    for record in event['Records']:
        index_item = {}
        reko_response = get_reko_response(record)
        if reko_response is not None:
            index_item['objectKey'] = record['s3']['object']['key']
            id = index_item['objectKey']
            index_item["bucket"] = record['s3']['bucket']['name']
            index_item["createdTimestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            index_item["labels"] = []
            labels = reko_response['Labels']

            for label in labels:
                index_item["labels"].append(label['Name'])
            
            # url = ES_HOST + '/' + 'photos' + '/' + 'Photo'
            index_item = json.dumps(index_item)
            url = ES_ENDPOINT + '/' + ES_INDEX + '/' + ES_TYPE + '/'
            req = http.request('POST', url + str(id), body = index_item, headers = { "Content-Type": "application/json" }, retries = False)
    
    return {
        'statusCode': 200,
        'headers': cors,
        'body': json.dumps("Label(s) are detected successfully ")
    }


def get_reko_response(record):
    reko = boto3.client('rekognition')
    bucket_name = record['s3']['bucket']['name']
    object_key = record['s3']['object']['key']
    reko_response = reko.detect_labels(
        Image={
            'S3Object': {
                'Bucket': bucket_name,
                'Name': object_key,
            },
        },
        MaxLabels=110,
        MinConfidence=70,
    ) 

    return reko_response






