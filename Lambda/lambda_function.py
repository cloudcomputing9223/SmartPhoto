import json
import logging
import es_handler
import lex_handler
import lex_execution
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
        logger.debug('An API Gateway event')
        lex_req = event['queryStringParameters']['q']
        
        # generate unique user ID using timestamp
        current_time_strings = str(time.time()).split(".") 
        user_id = current_time_strings[0]
        
        response = lex_handler.query_lex(user_id, lex_req.replace('_', ' '))
        logger.debug(response)
        
        print('response data is: ')
        print(response)
        keywords = response['slots']
       
        logger.debug('Keywords from lex request: {}'.format(keywords))
        
        #if keywords['photoTypeA'] and keywords['photoTypeB']:
        labels = []
        if keywords['photoTypeA'] != None:
            labels.append(keywords['photoTypeA'])
        if keywords['photoTypeB']!= None and keywords['photoTypeB'].lower() != keywords['photoTypeA'].lower():
            labels.append(keywords['photoTypeB'])
        print(labels)

        body = {
            'photos': search_photos_by_labels(ES_HOST, ES_INDEX, labels, 10),
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

def query_lex(user_id, req):
    client = boto3.client('lex-runtime')
    response = client.post_text(
        botName='album',
        botAlias='asdasd',
        userId=user_id,
        sessionAttributes={},
        requestAttributes={},
        inputText=req
    )
    logger.debug(response)

    return response

def search_photos_by_labels(es_host_endpoint, index, labels, size):
    # logger.debug(endpoint)
    # logger.debug(index)

    response = requests.post(
        es_host_endpoint + "/" + index + "/Photo/_search", 
        json={
            "size": str(size),
            "from": "0",
            "version": True,
            "query": {
                "bool": {
                    "filter": {
                        "bool": {
                            "should": compose_label_filter(labels)
                        }
                    }
                }
            }
        }
    )
    #return decode_response(response.text)
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

def compose_label_filter(labels):
    filters = []

    for label in labels:
        label_filter = {
            "term": {"labels": label}
        }
        filters.append(label_filter)

    return filters
    
def decode_response(response_text):
    response_obj = json.loads(response_text)
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


# def validate_bot_request(intent_request):
#     """
#     Called when the user specifies an intent for this bot.
#     """

#     current_intent = intent_request['currentIntent']
#     intent_name = current_intent['name']
#     logger.debug(
#         'dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_name))

#     keywords = []
    
#     if intent_name == 'SearchIntent':
#         validation_result = validate_keywords(current_intent['slots'])
#         logger.debug('Bot request validation result is {}'.format(validation_result))
        
#         session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}

#         if not validation_result['isValid']:
#             slots = current_intent['slots']
#             slots[validation_result['violatedSlot']] = None

#             return elicit_slot(
#                 session_attributes,
#                 current_intent['name'],
#                 slots,
#                 validation_result['violatedSlot'],
#                 validation_result['message']
#             )
            
#         # session_attributes['currentCriteria'] = criteria_json
#         return delegate(session_attributes, current_intent['slots'])

#     raise Exception('Intent with name ' + intent_name + ' not supported')

# def validate_keywords(slots):
#     keyword_a = try_ex(lambda: slots['KeywordA'])
#     keyword_b = try_ex(lambda: slots['KeywordB'])
    
#     logger.debug('keywords to be validated are {} and {}'.format(keyword_a, keyword_b))

#     if not keyword_a:
#         return build_validation_result(
#             False,
#             'KeywordA',
#             'I did not understand the first keyword you are looking for. Please try another keyword or say \'Nothing\''
#         )

#     if not keyword_b:
#         return build_validation_result(
#             False,
#             'KeywordB',
#             'I did not understand the second keyword you are looking for. Please try another keyword or say \'Nothing\''
#         )

#     return {'isValid': True}

# def delegate(session_attributes, slots):
#     return {
#         'sessionAttributes': session_attributes,
#         'dialogAction': {
#             'type': 'Delegate',
#             'slots': slots
#         }
#     }

# def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
#     return {
#         'sessionAttributes': session_attributes,
#         'dialogAction': {
#             'type': 'ElicitSlot',
#             'intentName': intent_name,
#             'slots': slots,
#             'slotToElicit': slot_to_elicit,
#             'message': message
#         }
#     }

# def try_ex(func):
#     """
#     Call passed in function in try block. If KeyError is encountered return None.
#     This function is intended to be used to safely access dictionary.

#     Note that this function would have negative impact on performance.
#     """

#     try:
#         return func()
#     except KeyError:
#         return None
        
# def build_validation_result(isvalid, violated_slot, message_content):
#     return {
#         'isValid': isvalid,
#         'violatedSlot': violated_slot,
#         'message': {'contentType': 'PlainText', 'content': message_content}
#     }








#######################not sure if same as above tester########################################




import json
import logging
import es_handler
import lex_handler
import lex_execution
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
        logger.debug('An API Gateway event')
        lex_req = event['queryStringParameters']['q']
        
        # generate unique user ID using timestamp
        current_time_strings = str(time.time()).split(".") 
        user_id = current_time_strings[0]
        
        response = lex_handler.query_lex(user_id, lex_req.replace('_', ' '))
        logger.debug(response)
        
        print('response data is: ')
        print(response)
        keywords = response['slots']
       
        logger.debug('Keywords from lex request: {}'.format(keywords))
        
        #if keywords['photoTypeA'] and keywords['photoTypeB']:
        labels = []
        if keywords['photoTypeA'] != None:
            labels.append(keywords['photoTypeA'])
        if keywords['photoTypeB']!= None and keywords['photoTypeB'].lower() != keywords['photoTypeA'].lower():
            labels.append(keywords['photoTypeB'])
        print(labels)

        body = {
            'photos': search_photos_by_labels(ES_HOST, ES_INDEX, labels, 10),
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

def query_lex(user_id, req):
    client = boto3.client('lex-runtime')
    response = client.post_text(
        botName='album',
        botAlias='asdasd',
        userId=user_id,
        sessionAttributes={},
        requestAttributes={},
        inputText=req
    )
    logger.debug(response)

    return response

def search_photos_by_labels(es_host_endpoint, index, labels, size):
    # logger.debug(endpoint)
    # logger.debug(index)

    response = requests.post(
        es_host_endpoint + "/" + index + "/Photo/_search", 
        json={
            "size": str(size),
            "from": "0",
            "version": True,
            "query": {
                "bool": {
                    "filter": {
                        "bool": {
                            "should": compose_label_filter(labels)
                        }
                    }
                }
            }
        }
    )
    #return decode_response(response.text)
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


def compose_label_filter(labels):
    filters = []

    for label in labels:
        label_filter = {
            "term": {"labels": label}
        }
        filters.append(label_filter)

    return filters
    
def decode_response(response_text):
    response_obj = json.loads(response_text)
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


# def validate_bot_request(intent_request):
#     """
#     Called when the user specifies an intent for this bot.
#     """

#     current_intent = intent_request['currentIntent']
#     intent_name = current_intent['name']
#     logger.debug(
#         'dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_name))

#     keywords = []
    
#     if intent_name == 'SearchIntent':
#         validation_result = validate_keywords(current_intent['slots'])
#         logger.debug('Bot request validation result is {}'.format(validation_result))
        
#         session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}

#         if not validation_result['isValid']:
#             slots = current_intent['slots']
#             slots[validation_result['violatedSlot']] = None

#             return elicit_slot(
#                 session_attributes,
#                 current_intent['name'],
#                 slots,
#                 validation_result['violatedSlot'],
#                 validation_result['message']
#             )
            
#         # session_attributes['currentCriteria'] = criteria_json
#         return delegate(session_attributes, current_intent['slots'])

#     raise Exception('Intent with name ' + intent_name + ' not supported')

# def validate_keywords(slots):
#     keyword_a = try_ex(lambda: slots['KeywordA'])
#     keyword_b = try_ex(lambda: slots['KeywordB'])
    
#     logger.debug('keywords to be validated are {} and {}'.format(keyword_a, keyword_b))

#     if not keyword_a:
#         return build_validation_result(
#             False,
#             'KeywordA',
#             'I did not understand the first keyword you are looking for. Please try another keyword or say \'Nothing\''
#         )

#     if not keyword_b:
#         return build_validation_result(
#             False,
#             'KeywordB',
#             'I did not understand the second keyword you are looking for. Please try another keyword or say \'Nothing\''
#         )

#     return {'isValid': True}

# def delegate(session_attributes, slots):
#     return {
#         'sessionAttributes': session_attributes,
#         'dialogAction': {
#             'type': 'Delegate',
#             'slots': slots
#         }
#     }

# def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
#     return {
#         'sessionAttributes': session_attributes,
#         'dialogAction': {
#             'type': 'ElicitSlot',
#             'intentName': intent_name,
#             'slots': slots,
#             'slotToElicit': slot_to_elicit,
#             'message': message
#         }
#     }

# def try_ex(func):
#     """
#     Call passed in function in try block. If KeyError is encountered return None.
#     This function is intended to be used to safely access dictionary.

#     Note that this function would have negative impact on performance.
#     """

#     try:
#         return func()
#     except KeyError:
#         return None
        
# def build_validation_result(isvalid, violated_slot, message_content):
#     return {
#         'isValid': isvalid,
#         'violatedSlot': violated_slot,
#         'message': {'contentType': 'PlainText', 'content': message_content}
#     }

