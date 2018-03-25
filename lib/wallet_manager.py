from Crypto.PublicKey import RSA
import base64

from lib.wallet import Wallet

class WalletManager:
    def add_user(self, username):
        wallet = Wallet(user=username)
        return wallet
    
    def get_user(self, wallet_id):
        wallet = Wallet()
        wallet.load(wallet_id=wallet_id)
        return wallet

    def check_user(self, user):
        return self.get_user(user) != None