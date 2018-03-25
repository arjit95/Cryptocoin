# core dependencies
import json
import shutil
import os

# 3rd party dependencies
from flask import Flask, render_template, request

# library dependencies
from lib.wallet_manager import WalletManager
from lib.blockchain import BlockChain, Block
from lib.wallet import Wallet, Transaction
from lib.transaction_io import TransactionOutput

# cleanup any previously created directory
shutil.rmtree('wallets/', ignore_errors=True)
os.mkdir('wallets')

app = Flask(__name__)

 # starting amount to be released on creating the blockchain
GENESIS_AMOUNT = 1000.

manager = WalletManager()
users = {}
genesis_wallet = None

# create the block chain
block_chain = BlockChain()

@app.route('/')
def serve():
    return render_template('index.html')

@app.route('/api', methods=['POST'])
def api():
    operation = request.form.get('operation')
    resp = {}

    if operation == 'add': # create a new user wallet
        if genesis_wallet.get_balance() < 50.:
            resp['code'] = 500
            resp['message'] = 'Server full cannot add new users.'
        
        else:
            username = request.form.get('username')
            wallet = manager.add_user(username)
            users[wallet.wallet_id] = wallet
            wallet.save() # save the wallet to disk.

            # add 50 coins to new user's wallet upon signup. 
            last_block = block_chain.get_block(block_chain.size() - 1)
            transaction = genesis_wallet.send_funds(wallet.public_key, 50.)
            add_block(last_block.hash, transaction)

            resp['code'] = 200
            resp['message'] = "User added and a wallet is created"
            resp['info'] = {
                'balance': wallet.get_balance(),
                'id': wallet.wallet_id
            }

    elif operation == 'list': # list all the online users to whom the amount can be transferred
        resp['code'] = 200
        resp['message'] = "List generated successfully"
        users_list = []
        for wallet_id in users.keys():
            users_list.append({
                'id': wallet_id,
                'name': users[wallet_id].user
            })

        resp['info'] = {'users_list': users_list}

    elif operation == 'fetch':
        wallet_id = request.form.get('wallet_id')
        if wallet_id in users:
            wallet = users[wallet_id]

            resp['code'] = 200
            resp['message'] = 'Info fetched successfully'
            resp['info'] = {
                'balance': wallet.get_balance(),
                'id': wallet_id
            }
        else:
            resp['code'] = 500
            resp['message'] = 'Cannot find wallet info in logged in users.'

    elif operation == 'login': # user login
        wallet_id = request.form.get('wallet_id')
        if manager.check_user(wallet_id):
            wallet = manager.get_user(wallet_id)
            users[wallet.wallet_id] = wallet

            resp['code'] = 200
            resp['message'] = "User logged in successfully"
            resp['info'] = {
                'balance': wallet.get_balance(),
                'id': wallet_id
            }
        else:
            resp['code'] = 500
            resp['message'] = "User does not exists with the name"

    elif operation == 'logout':
        wallet_id = request.form.get('wallet_id')
        if wallet_id in users:
            wallet = users[wallet_id]
            wallet.save()
            del users[wallet_id]

            resp['code'] = 200
            resp['message'] = "User logged out successfully"
        else:
            resp['code'] = 500
            resp['message'] = "User cannot be logged out"

    elif operation == 'transact':
        sender = request.form.get('sender') # sender wallet id
        receiver = request.form.get('receiver') # receiver wallet id
        amount = float(request.form.get('amount'))

        sender_wallet = users[sender]
        receiver_wallet = Wallet()
        receiver_wallet.load(receiver)

        if sender_wallet.get_balance() < amount:
            resp['code'] = 500
            resp['message'] = "Low balance, cannot proceed with transaction"
        else:
            last_block = block_chain.get_block(block_chain.size() - 1)
            transaction = sender_wallet.send_funds(receiver_wallet.public_key, amount)
            add_block(last_block.hash, transaction)
            resp['code'] = 200
            resp['message'] = "Transaction successful"
            resp['info'] = {
                'balance': sender_wallet.get_balance(),
                'transaction_id': transaction.transaction_id
            }

    else:
        resp['code'] = 500
        resp['message'] = "Unknown operation"
    
    return json.dumps(resp)

def add_block(prev_hash, transaction):
    block = Block(prev_hash)
    block.add_transaction(transaction)
    block_chain.add(block)


if __name__ == '__main__':
    # create the genesis block
    coinbase = Wallet()
    genesis_wallet = Wallet()

    genesis_transaction = Transaction(coinbase.public_key, genesis_wallet.public_key, GENESIS_AMOUNT, None)
    genesis_transaction.gen_signature(coinbase.private_key)	 # manually sign the genesis transaction
    genesis_transaction.transaction_id = "0" # set the transaction id

    # add the Transactions Output
    genesis_output = TransactionOutput(
        genesis_transaction.receiver
        , genesis_transaction.amount
        , genesis_transaction.transaction_id
    )
    genesis_transaction.transaction_outputs.append(genesis_output)

    BlockChain.UTXOs[genesis_output.id] = genesis_output
    add_block("0", genesis_transaction)

    users[genesis_wallet.wallet_id] = genesis_wallet
    genesis_wallet.save()

    app.run(host="0.0.0.0", port=8080, threaded=True)
