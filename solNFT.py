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
from PIL import Image, ImageDraw, ImageFont
import io
import qrcode
import datetime


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

        self.NFT_TEMPLATE = Image.open(file_dir + '/template.png')
        self.NAME_FONT = ImageFont.truetype(file_dir + '/PlusJakartaSans-Bold.ttf', 31)
        self.OTH_FONT = ImageFont.truetype(file_dir + '/Roboto-Regular.ttf', 20)
        self.COUNT_FONT = ImageFont.truetype(file_dir + '/RobotoMono-Bold.ttf', 53)


    def mintNFT(self, address, name, twitter_username, count):
        # checking address, name, count and uri as non null
        status, output = self._validate_params(address, name, count, twitter_username)
        if status is False:
            return output

        try:
            img, date_time = self._generateImage(address, name, count, twitter_username)
            img_uri = self._uploadImageOnArweave(img)
            metadata = self._getImageNFTMetadata(name, count, img_uri)
            metadata_uri = self._uploadMetadataOnArweave(metadata)
        except Exception as err:
            return {"status": "failure", "error": err}
        try:
            mint_token_id = self._mintNFT(address, metadata_uri, count)
        except Exception as err:
            return {"status": "failure", "error": err}
        return {"status": "success", "metadata":metadata, "metadata_uri":metadata_uri, "mint_token_id":mint_token_id, "datetime":date_time}

    def _generateImage(self, address, name, count, twitter_username):
        print("Generating NFT Image for "+str(twitter_username))
        img = self.NFT_TEMPLATE.copy()
        draw = ImageDraw.Draw(img)
        addr = address[0:4] + "..." + address[-4:]
        date_time = datetime.datetime.now().strftime("%d/%m/%Y %H:%M %p")
        if len(name)<=20:
            draw.text(xy=(132,290),text=name,fill=(0,0,0),font=self.NAME_FONT)
        else:
            draw.text(xy=(132,290),text=name[0:17]+"...",fill=(0,0,0),font=self.NAME_FONT)
        draw.text(xy=(132,375),text=date_time,fill=(0,0,0),font=self.OTH_FONT)
        draw.text(xy=(482,375),text=addr,fill=(0,0,0),font=self.OTH_FONT)
        draw.text(xy=(600,180),text="#"+str(count),fill=(0,0,0),font=self.COUNT_FONT)
        qr = qrcode.make('https://superteam.fun/'+address).resize((94,94))
        img.paste(qr,(680,320))
        return img, date_time

    def _uploadImageOnArweave(self, img):
        print("Uploading NFT Image to Arweave")
        output = io.BytesIO()
        img.save(output, format="png")
        img_as_string = output.getvalue()
        attempts = 0
        err_msg=""
        while attempts < 3:
            try:
                if attempts > 0:
                    print("retrying... ("+str(attempts+1)+")")
                transaction = arTransaction(self.ar_wallet, data=img_as_string)
                transaction.add_tag('Content-Type', 'image/jpeg')
                transaction.sign()
                transaction.send()
                break
            except Exception as err:
                err_msg=err
                attempts += 1
        if attempts == 3:
            raise Exception(err_msg)
        return API_URL+"/"+transaction.id

    def _mintNFT(self, address, metadata_uri, count):
        print("Deploying token account for NFT No. "+str(count))
        deployed = self.metaplex_api.deploy(self.api_endpoint, "Web3Visa #"+str(count), "web3-visa")
        deployed_json = json.loads(deployed)
        print("Minting NFT No. "+str(count))
        stats = self.metaplex_api.mint(self.api_endpoint, deployed_json['contract'], address, metadata_uri)
        print("Mint successful!")
        return deployed_json['contract']

    def _uploadMetadataOnArweave(self, metadata):
        print("Uploading metadata on Arweave")
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
        metadata['animation_url'] = uri
        metadata['name'] = metadata['name'] + str(count)
        metadata['attributes'][0]['value'] = name
        metadata['attributes'][1]['value'] = count
        metadata['properties']['files'][0]['uri'] = uri
        return metadata

    def _validate_params(self, address, name, count, twitter_username):
        if address is None or address == "":
            return False, {"status": "failure", "error": "address cannot be null"}
        if len(address)<32 or len(address)>44:
            return False, {"status": "failure", "error": "invalid address"}
        if name is None or name == "":
            return False, {"status": "failure", "error": "name cannot be null"}
        if count is None:
            return False, {"status": "failure", "error": "count cannot be null"}
        if twitter_username is None or twitter_username == "":
            return False, {"status": "failure", "error": "twitter_username cannot be null"}
        return True, {}

    def update_NFT(self, mint_token_id, video_link, name, count, max_retries=3, max_timeout=60):
        """
        Updates the json metadata for a given mint token id.
        """
        try:
            video_metadata = self._getVideoNFTMetadata(name, count, video_link)
            video_metadata_uri = self._uploadMetadataOnArweave(video_metadata)
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