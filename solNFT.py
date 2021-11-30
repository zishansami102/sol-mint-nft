from api.metaplex_api import MetaplexAPI
import base58
from solana.keypair import Keypair
from cryptography.fernet import Fernet
import json
from arweave.arweave_lib import Wallet, Transaction, API_URL

class SolNFT(object):
    def __init__(self, pvt_key, ar_wallet, api_endpoint='https://api.devnet.solana.com/', file_dir='./files'):
        decoded_pvt_key = base58.b58decode(pvt_key)
        account = Keypair.from_secret_key(decoded_pvt_key)
        cfg = {"PRIVATE_KEY": decoded_pvt_key, "PUBLIC_KEY": str(account.public_key), "DECRYPTION_KEY": Fernet.generate_key().decode("ascii")}
        self.metaplex_api = MetaplexAPI(cfg)

        self.api_endpoint = api_endpoint
        self.ar_wallet = Wallet(ar_wallet)
        self.metadata_template = json.load(open(file_dir + '/metadata_video.json'))

    def mintNFT(self, address, name, count, uri):
        # checking address, name, count and uri as non null
        status, output = self._validate_params(address, name, count, uri)
        if status is False:
            return output

        try:
            print("Uploading metadata on Arweave")
            metadata_uri, metadata = self.uploadMetadataOnArweave(name, count, uri)
        except Exception as err:
            return {"status": "failure", "error": err}
        try:
            mint_address = self._mintNFT(address, metadata_uri, count)
        except Exception as err:
            return {"status": "failure", "error": err}
        return {"status": "success", "metadata":metadata, "metdata_uri":metadata_uri, "mint_address":mint_address}
        

    def _mintNFT(self, address, metadata_uri, count):
        print("Deploying token account for NFT No. "+str(count))
        deployed = self.metaplex_api.deploy(self.api_endpoint, "Web3Visa #"+str(count), "web3-visa")
        deployed_json = json.loads(deployed)
        print("Minting NFT No. "+str(count))
        stats = self.metaplex_api.mint(self.api_endpoint, deployed_json['contract'], address, metadata_uri)
        print("Mint successful!")

    def uploadMetadataOnArweave(self, name, count, uri):
        metadata = self.getNFTMetadata(name, count, uri)

        attempts = 0
        err_msg=""
        while attempts < 3:
            try:
                if attempts > 0:
                    print("retrying... ("+str(attempts+1)+")")
                transaction = Transaction(self.ar_wallet, data=json.dumps(metadata))
                transaction.add_tag('Content-Type', 'text/html')
                transaction.sign()
                transaction.send()
                break
            except Exception as err:
                err_msg=err
                attempts += 1
        if attempts == 3:
            raise Exception(err_msg)
        return API_URL+"/"+transaction.id, metadata
        
    def getNFTMetadata(self, name, count, uri):
        metadata = self.metadata_template.copy()
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