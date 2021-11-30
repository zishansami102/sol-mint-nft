import argparse
from api.metaplex_api import MetaplexAPI
from solana.rpc.api import Client
import base58
from solana.keypair import Keypair
from cryptography.fernet import Fernet
import json
from arweave.arweave_lib import Wallet, Transaction
from PIL import Image, ImageDraw, ImageFont
import io
import qrcode

# Your Wallet private key from where to pay transaction and mint fee
PVT_KEY = 'your_pvt_key'

decoded_pvt_key = base58.b58decode(PVT_KEY)
account = Keypair.from_secret_key(decoded_pvt_key)
cfg = {"PRIVATE_KEY": decoded_pvt_key, "PUBLIC_KEY": str(account.public_key), "DECRYPTION_KEY": Fernet.generate_key().decode("ascii")}
metaplex_api = MetaplexAPI(cfg)
api_endpoint = "https://api.devnet.solana.com/"

DIR_NAME = "./files/"
# NFT Image params
NFT_TEMPLATE = Image.open(DIR_NAME + 'visa.png')
FONT = ImageFont.truetype(DIR_NAME + 'Raleway-Medium.ttf', 18)

AR_WALLET = Wallet(DIR_NAME + 'arweave-keyfile-Lhqy4YQu1UzD8iib3VR8QBo0NT8r6ayvxuCJpa-natY.json')
METADATA_TEMPLATE = json.load(open(DIR_NAME + 'metadata.json'))

def generateAndMintNFT(address, meta):
    metadata_uri = generateAndUploadImage(address, meta)
    mintNFT(address, metadata_uri, meta)

def mintNFT(address, metadata_uri, meta):
    deployed = metaplex_api.deploy(api_endpoint, "Web3Visa #"+str(meta["count"]), "web3-visa")
    deployed_json = json.loads(deployed)
    stats = metaplex_api.mint(api_endpoint, deployed_json['contract'], address, metadata_uri)
    print("Mint successful!")

def generateAndUploadImage(address, meta):
    nft_img = generateImage(address, meta)
    print("image generated")
    meta_uri = uploadImageOnArweave(nft_img, meta)
    print("image uploaded on Arweave, meta_uri: "+meta_uri)
    return meta_uri

def generateImage(address, meta):
    img = NFT_TEMPLATE.copy()
    draw = ImageDraw.Draw(img)
    draw.text(xy=(100,50),text=meta["name"],fill=(255,255,255),font=FONT)
    draw.text(xy=(50,50),text="#"+str(meta["count"]),fill=(255,255,255),font=FONT)
    qr = qrcode.make('superteam.fun/'+meta["name"]).resize((60,60))
    img.paste(qr,(300,60))
    return img

def uploadImageOnArweave(img, meta):
    output = io.BytesIO()
    img.save(output, format="png")
    img_as_string = output.getvalue()
    transaction = Transaction(AR_WALLET, data=img_as_string)
    transaction.add_tag('Content-Type', 'image/jpeg')
    transaction.sign()
    transaction.send()
    metadata = getNFTMetadata(transaction.id, meta)
    transaction = Transaction(AR_WALLET, data=json.dumps(metadata))
    transaction.add_tag('Content-Type', 'text/html')
    transaction.sign()
    transaction.send()
    return "https://arweave.net/"+transaction.id
    
def getNFTMetadata(arweave_img_id, meta):
    metadata = METADATA_TEMPLATE.copy()
    metadata['image']='https://www.arweave.net/'+arweave_img_id
    metadata['name']=metadata['name']+str(meta["count"])
    metadata['attributes'][0]['value']=meta["name"]
    metadata['attributes'][1]['value']=meta["count"]
    return metadata
    

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--wallet-address", default=None)
    ap.add_argument("--user-name", default=None)
    ap.add_argument("--nft-count", default=None)
    args = ap.parse_args()
    if args.wallet_address == None:
        print("wallet-address argument missing ")
    else:
        meta = {"name":"Zishan Sami", "count":100}
        if args.user_name != None:
            meta["name"] = args.user_name
        if args.nft_count != None:
            meta["count"] = args.nft_count
        generateAndMintNFT(args.wallet_address, meta)