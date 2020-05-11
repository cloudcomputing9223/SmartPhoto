import json
import logging
import time
import boto3
from botocore.vendored import requests

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

ES_HOST = 'https://vpc-photos-em6q2gg7sstox7upwcuobtl7ym.us-east-1.es.amazonaws.com'
ES_INDEX = 'photos'

def lambda_handler(event, context):
    logger.debug(json.dumps(event))

    if 'path' in event:
        logger.debug('FROM API GATEWAY')
        lex_req = event['queryStringParameters']['q']
        
        # generate unique user ID using timestamp
        current_time_strings = str(time.time()).split(".") 
        user_id = current_time_strings[0] # unique-fy 
        client = boto3.client('lex-runtime')
        response = client.post_text(
            botName='album',
            botAlias='asdasd',
            userId=user_id,
            sessionAttributes={},
            requestAttributes={},
            inputText=lex_req.replace('_', ' ')
        )
        logger.debug(response)
        
        print('response data is: ')
        print(response)
        keywords = response['slots']     
        logger.debug('Keywords from lex request: {}'.format(keywords))
        
        labels = []
        if keywords['photoTypeA'] != None:
            labels.append(keywords['photoTypeA'])
        if keywords['photoTypeB']!= None and keywords['photoTypeB'].lower() != keywords['photoTypeA'].lower():
            labels.append(keywords['photoTypeB'])
        print(labels)

        body = {
            'photos': search_photos_from_ES(labels, 10),
            'message': 'Got it! Displaying photos for ' + ' and '.join(labels)
        }
        return {
            'statusCode': 200,
            'headers': {
                "Access-Control-Allow-Origin":"*",
                "Access-Control-Allow-Methods":"GET,OPTIONS",
                "Access-Control-Allow-Headers":"Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Content-Type":"application/json"
            },
            'body': json.dumps(body)
        }
        
    else:
        raise Exception('Event not supported ' + json.dumps(event))

def search_photos_from_ES(labels, size):
    response = requests.post(
        ES_HOST + "/" + ES_INDEX + "/Photo/_search", 
        json={
            "size": str(size),
            "from": "0",
            "version": True,
            "query": {
                "bool": {
                    "filter": {
                        "bool": {
                            "should": label_filters(labels)
                        }
                    }
                }
            }
        }
    )
    response_obj = json.loads(response.text)
    logger.debug(response_obj)
    hits = response_obj['hits']['hits']
    photos = []
    for hit in hits:
        photo = {
            "bucket": hit['_source']['bucket'],
            "objectKey": hit['_source']['objectKey']
        }
        photos.append(photo)

    return photos


def label_filters(labels):
    filters = []
    for label in labels:
        label_filter = {
            "term": {"labels": label}
        }
        filters.append(label_filter)

    return filters
    


