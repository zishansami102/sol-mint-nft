import json
from solNFT import SolNFT
import os
import boto3
from enum import Enum

# change
dynamodb = None
FILE_DIR = "./files/"
AR_WALLET = 'arweave-keyfile-Lhqy4YQu1UzD8iib3VR8QBo0NT8r6ayvxuCJpa-natY.json'

class NFTGenStatus(Enum):
    NOT_STARTED = "NOT_STARTED"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"

if os.environ.get("ENVIRON") == "DEBUG":
    dynamodb = boto3.resource('dynamodb', endpoint_url="http://localhost:8000", region_name="local")
else:
    dynamodb = boto3.resource('dynamodb', region_name=os.environ.get("REGION"))
user_table = dynamodb.Table('users')
nft_table = dynamodb.Table('nfts')
pvt_key = os.environ.get("PRIVATE_KEY")



def updateNftStatus(twitter_uid, status):
    user_table.update_item(
        Key={
            'twitter_uid': twitter_uid
        },
        UpdateExpression='SET nft_gen_status = :ngs',
        ExpressionAttributeValues={
            ':ngs': status
        }
    )


def hello(event, context):
    sol_nft_object = SolNFT(pvt_key=pvt_key, ar_wallet=FILE_DIR + AR_WALLET, file_dir=FILE_DIR)
    # changes
    print(event)
    event_body = json.loads(event['Records'][0]['body'])
    print(event_body)
    currentStatus = user_table.get_item(
        Key={
            'twitter_uid': event_body['twitter_uid']
        }
    )
    print(currentStatus)
    if currentStatus['Item']['nft_gen_status'] != NFTGenStatus.NOT_STARTED.value:
        print("already minted / minting for " + event_body['twitter_uid'])
        return
    updateNftStatus(event_body['twitter_uid'], NFTGenStatus.STARTED.value)


    result = sol_nft_object.mintNFT(address=event_body['address'], name=event_body['name'], twitter_username=event_body['name'], count=event_body['count'])

    # result = {
    #     'status': 'success',
    #     'metadata': {
    #         'metadata': 'metadata'
    #     },
    #     'metdata_uri': 'metdata_uri',
    #     'mint_token_id': 'mint_token_id'
    # }
    print(result)

    if result['status'] != 'success':
        ## Handle errors
        user_table.update_item(
            Key={
                'twitter_uid': event_body['twitter_uid']
            },
            UpdateExpression='SET nft_error=:ne, nft_gen_status = :ngs',
            ExpressionAttributeValues={
                ':ne': result['error'],
                ':ngs': NFTGenStatus.FAILURE.value
            }
        )
        return
    
    metadata = result["metadata"]
    metdata_uri = result["metadata_uri"]
    mint_token_id = result["mint_token_id"]


    user_table.update_item(
        Key={
            'twitter_uid': event_body['twitter_uid']
        },
        UpdateExpression='SET mint_token_id=:mti, metdata_uri=:mu, is_mint_successfull=:ims, nft_gen_status = :ngs, nft_image_uri=:niu',
        ExpressionAttributeValues={
            ':mti': mint_token_id,
            ':mu': metdata_uri,
            ':ims': True,
            ':ngs': NFTGenStatus.SUCCESS.value,
            ':niu': metadata['image']
        }
    )

    response = user_table.get_item(
        Key={
            'twitter_uid': event_body['twitter_uid']
        }
    )

    print(response['Item'])

    return
