from arweave.arweave_lib import Wallet, Transaction, API_URL

class ArweaveUploader(object):
    def __init__(self, arweave_wallet='./files/arweave-keyfile-Lhqy4YQu1UzD8iib3VR8QBo0NT8r6ayvxuCJpa-natY.json'):
        self.AR_WALLET = Wallet(arweave_wallet)

    def upload(self, video_path):
        try:
            with open(video_path, 'rb') as my_video:
                video_in_bytes = my_video.read()
        except FileNotFoundError as err:
            print("Arwevae uplaod failed, requested file not found: " + video_path)
            return {"status":"failure", "error":err}

        attempts = 0
        err_msg = ""
        while attempts < 3:
            try:
                if attempts > 0:
                    print("retrying... ("+str(attempts+1)+")")
                transaction = Transaction(self.AR_WALLET, data=video_in_bytes)
                transaction.add_tag('Content-Type', 'video/mp4')
                transaction.sign()
                transaction.send()
                break
            except Exception as err:
                print(err)
                err_msg = err
                attempts += 1
        if attempts == 3:
            print("Not able to upload to arweave: " + video_path)
            return {"status":"failure", "error":err_msg}
        return {"status":"success", "uri":API_URL+"/"+transaction.id}

        
