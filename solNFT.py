from api.metaplex_api import MetaplexAPI
import base58
from solana.keypair import Keypair
from solana.publickey import PublicKey
from solana.transaction import Transaction
from cryptography.fernet import Fernet
import json
from arweave.arweave_lib import Wallet, Transaction as arTransaction, API_URL
from solana.rpc.api import Client
from metaplex.metadata import (
    get_metadata,
    update_metadata_instruction_data,
    update_metadata_instruction
)
from utils.execution_engine import execute


class SolNFT(object):
    def __init__(self, pvt_key, ar_wallet, api_endpoint='https://api.devnet.solana.com/', file_dir='./files'):
        decoded_pvt_key = base58.b58decode(pvt_key)
        self.account = Keypair.from_secret_key(decoded_pvt_key)
        cfg = {"PRIVATE_KEY": decoded_pvt_key, "PUBLIC_KEY": str(self.account.public_key), "DECRYPTION_KEY": Fernet.generate_key().decode("ascii")}
        self.metaplex_api = MetaplexAPI(cfg)

        self.api_endpoint = api_endpoint
        self.ar_wallet = Wallet(ar_wallet)
        self.metadata_video_template = json.load(open(file_dir + '/metadata_video.json'))
        self.metadata_image_template = json.load(open(file_dir + '/metadata_image.json'))

    def mintNFT(self, address, name, count, uri):
        # checking address, name, count and uri as non null
        status, output = self._validate_params(address, name, count, uri)
        if status is False:
            return output

        try:
            metadata = self._getImageNFTMetadata(name, count, uri)
            print("Uploading metadata on Arweave")
            metadata_uri = self.uploadMetadataOnArweave(metadata)
        except Exception as err:
            return {"status": "failure", "error": err}
        try:
            mint_token_id = self._mintNFT(address, metadata_uri, count)
        except Exception as err:
            return {"status": "failure", "error": err}
        return {"status": "success", "metadata":metadata, "metdata_uri":metadata_uri, "mint_token_id":mint_token_id}
        

    def _mintNFT(self, address, metadata_uri, count):
        print("Deploying token account for NFT No. "+str(count))
        deployed = self.metaplex_api.deploy(self.api_endpoint, "Web3Visa #"+str(count), "web3-visa")
        deployed_json = json.loads(deployed)
        print("Minting NFT No. "+str(count))
        stats = self.metaplex_api.mint(self.api_endpoint, deployed_json['contract'], address, metadata_uri)
        print("Mint successful!")
        return deployed_json['contract']

    def uploadMetadataOnArweave(self, metadata):
        attempts = 0
        err_msg=""
        while attempts < 3:
            try:
                if attempts > 0:
                    print("retrying... ("+str(attempts+1)+")")
                transaction = arTransaction(self.ar_wallet, data=json.dumps(metadata))
                transaction.add_tag('Content-Type', 'text/html')
                transaction.sign()
                transaction.send()
                break
            except Exception as err:
                err_msg=err
                attempts += 1
        if attempts == 3:
            raise Exception(err_msg)
        return API_URL+"/"+transaction.id

    def _getImageNFTMetadata(self, name, count, uri):
        metadata = self.metadata_image_template.copy()
        metadata['image'] = uri
        metadata['name'] = metadata['name'] + str(count)
        metadata['attributes'][0]['value'] = name
        metadata['attributes'][1]['value'] = count
        return metadata
        
    def _getVideoNFTMetadata(self, name, count, uri):
        metadata = self.metadata_video_template.copy()
        metadata['image'] = uri
        metadata['animation_url'] = uri
        metadata['name'] = metadata['name'] + str(count)
        metadata['attributes'][0]['value'] = name
        metadata['attributes'][1]['value'] = count
        metadata['properties']['files'][0]['uri'] = uri
        return metadata

    def _validate_params(self, address, name, count, uri):
        if address is None:
            return False, {"status": "failure", "error": "address cannot be null"}
        if name is None:
            return False, {"status": "failure", "error": "name cannot be null"}
        if count is None:
            return False, {"status": "failure", "error": "count cannot be null"}
        if uri is None:
            return False, {"status": "failure", "error": "uri cannot be null"}
        return True, {}

    def update_NFT(self, mint_token_id, video_link, name, count, max_retries=3, max_timeout=60):
        """
        Updates the json metadata for a given mint token id.
        """
        try:
            video_metadata = self._getVideoNFTMetadata(name, count, video_link)
            video_metadata_uri = self.uploadMetadataOnArweave(video_metadata)
        except Exception as err:
            return {"status": "failure", "error": err}
        
        try:
            self._updateMetadata(mint_token_id, video_metadata_uri, max_retries, max_timeout)
        except Exception as err:
            return {"status": "failure", "error": err}
        return {"status": "success", "metadata":video_metadata, "metdata_uri":video_metadata_uri, "mint_token_id":mint_token_id}

    def _updateMetadata(self, mint_token_id, video_metadata_uri, max_retries=3, max_timeout=60, target=20, finalized=True):
        client = Client(self.api_endpoint)
        mint_account = PublicKey(mint_token_id)
        signers = [self.account]
        tx = Transaction()
        metadata = get_metadata(client, mint_account)
        update_metadata_data = update_metadata_instruction_data(
            metadata['data']['name'],
            metadata['data']['symbol'],
            video_metadata_uri,
            metadata['data']['seller_fee_basis_points'],
            metadata['data']['creators'],
            metadata['data']['verified'],
            metadata['data']['share'],
        )
        update_metadata_ix = update_metadata_instruction(
            update_metadata_data,
            self.account.public_key,
            mint_account,
        )
        tx = tx.add(update_metadata_ix)
        resp = execute(
            self.api_endpoint,
            tx,
            signers,
            max_retries=max_retries,
            skip_confirmation=True,
            max_timeout=max_timeout,
            target=target,
            finalized=finalized,
        )
        resp["status"] = 200
        return json.dumps(resp)