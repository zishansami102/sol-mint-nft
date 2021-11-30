import argparse
from solNFT import SolNFT

if __name__ == "__main__":
    # Your Wallet private key from where to pay transaction and mint fee
    PVT_KEY = 'your_pvt_key'
    FILE_DIR = "./files/"
    AR_WALLET = 'arweave-keyfile-Lhqy4YQu1UzD8iib3VR8QBo0NT8r6ayvxuCJpa-natY.json'
    
    sol_nft = SolNFT(PVT_KEY, FILE_DIR+AR_WALLET, file_dir=FILE_DIR)

    ap = argparse.ArgumentParser()
    ap.add_argument("--wallet-address", default=None)
    ap.add_argument("--file-uri", default=None)
    ap.add_argument("--name", default=None)
    ap.add_argument("--nft-count", default=None)
    
    args = ap.parse_args()
    if args.wallet_address == None:
        print("wallet-address argument missing ")
    elif args.file_uri == None:
        print("file-uri argument missing ")
    elif args.name== None:
        print("name argument missing ")
    elif args.nft_count == None:
        print("nft-count argument missing ")
    else:
        sol_nft.mintNFT(args.wallet_address, args.name, args.nft_count, args.file_uri)