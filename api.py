from api.metaplex_api import MetaplexAPI
from solana.rpc.api import Client
import base58
from solana.keypair import Keypair
from cryptography.fernet import Fernet
import json

pvt_key = '4UYFX6EdwUZXyaVyWpmznzGwta6h4y6PnRF6bsBXQTVrpifqEZwiDg82N3yVX8mKQK9E82Vynx94GV4UPiNwNA8n'
decoded_pvt_key = base58.b58decode(pvt_key)
key_pair = Keypair()
account = Keypair.from_secret_key(decoded_pvt_key)
cfg = {"PRIVATE_KEY": decoded_pvt_key, "PUBLIC_KEY": str(account.public_key), "DECRYPTION_KEY": Fernet.generate_key().decode("ascii")}
api_endpoint = "https://api.devnet.solana.com/"
cli = Client(api_endpoint)
metaplex_api = MetaplexAPI(cfg)
mint = metaplex_api.deploy(api_endpoint, "random_nilay_nft", "rnnft")
print(mint)
mint = json.loads(mint)
stats = metaplex_api.mint(api_endpoint, mint['contract'], 'CxiC2hDCs4tv4f9TGmT9UyYBYgsGPP4NdZWbV4QJDZC2', "https://arweave.net/OCKsx28GzAe2J_Nrb-szCkGCSejGPl-0UqT7u_EHdtQ/", supply=10)
print(stats)


# cfg = {
#     "PRIVATE_KEY": base58.b58encode(account.secret_key()).decode("ascii"),
#     "PUBLIC_KEY": str(account.public_key()),
#     "DECRYPTION_KEY": Fernet.generate_key().decode("ascii"),
# }