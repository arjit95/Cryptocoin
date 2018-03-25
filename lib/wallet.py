import base64
import pickle
import time

from Crypto import Random
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256

from lib.blockchain import BlockChain
from lib.transaction_io import TransactionOutput, TransactionInput

class Wallet:
	"""
	Description: Wallet class to handle all wallet related tasks,
	like loading, saving, transferring wallet funds etc.
	"""

	def __init__(self, user='Coinbase'):
		"""
		Descripiton: Creates a new wallet with the specified username.
		Note: The username typically is not required for this kind of wallet,
		but is easier to read hence we are using it here.

		Arguments:
		user: The username for the wallet.
		"""
		self.UTXOs = {} # unspent transactions
		self.user = user

		self.__gen_key_pair()
		
		digest = SHA256.new()
		digest.update(self.public_key.exportKey('PEM'))
		self.wallet_id = digest.hexdigest()

	def save(self):
		"""
		Description: Write wallet contents to disk. This file can be given to the user
		so that he can carry his wallet in a usb drive and can login using
		that drive.
		"""

		with open('wallets/' + self.wallet_id, 'wb') as f:
			obj = {
				'UTXOs': self.UTXOs,
				'private_key': self.private_key.exportKey('PEM'),
				'public_key': self.public_key.exportKey('PEM'),
				'user': self.user,
				'wallet_id': self.wallet_id
			}
			pickle.dump(obj, f, pickle.HIGHEST_PROTOCOL)

	def load(self, wallet_id):
		"""
		Description: Load Wallet contents from disk.

		Arguments:
		wallet_id - The wallet id assigned while creating a new wallet.
		"""
		wallet_id = wallet_id

		with open('wallets/' + wallet_id, 'rb') as f:
			obj = pickle.load(f)
			self.UTXOs = obj['UTXOs']
			self.__private_key = RSA.importKey(obj['private_key'])
			self.__public_key = RSA.importKey(obj['public_key'])
			self.user = obj['user']
			self.wallet_id = wallet_id

	def __gen_key_pair(self):
		"""
		Description: Generates a public-private keypair.
		"""

		modulus_length = 256 * 8
		self.__private_key = RSA.generate(modulus_length, Random.new().read)
		self.__public_key = self.private_key.publickey()

	@property
	def public_key(self):
		return self.__public_key

	@property
	def private_key(self):
		return self.__private_key

	@public_key.setter
	def public_key(self, value):
		raise RuntimeError('Cannot set public key value')

	@private_key.setter
	def private_key(self, value):
		raise RuntimeError('Cannot set private key value')

	def get_balance(self):
		"""
		Description: Gets the balance from the current wallet, and stores
		the unspent transactions in self.UTXOs

		Returns:
		The balance present in this wallet
		"""

		total = 0
		for item in BlockChain.UTXOs.keys():
			UTXO = BlockChain.UTXOs[item]

			if(UTXO.is_mine(self.public_key)): # if output belongs to me ( if coins belong to me )
				self.UTXOs[UTXO.id] =  UTXO # add it to our list of unspent transactions.
				total += UTXO.amount

		return total

	def send_funds(self, reciepient, value):
		"""
		Description: Send funds from one wallet to another

		Arguments:

		reciepient: The public key for the reciepient
		value: The amount to be sent to the reciepient

		Returns:
		A new transaction to send the requested amount to the reciepient
		"""

		# Generates and returns a new transaction from this wallet.
		if self.get_balance() < value: # gather balance and check funds.
			print("Not Enough funds to send transaction. Transaction Discarded.")
			return None

		# create array list of inputs
		inputs = []
		total = 0

		# collect all the inputs required to initiate the transaction
		for transaction_id in self.UTXOs.keys():
			UTXO = self.UTXOs[transaction_id]
			total += UTXO.amount
			inputs.append(TransactionInput(UTXO.id))

			if total > value:
				break

		new_transaction = Transaction(self.public_key, reciepient, value, inputs)
		new_transaction.gen_signature(self.private_key)

		# remove the collected inputs from unspent transactions
		for transaction in inputs:
			del self.UTXOs[transaction.transaction_id]

		return new_transaction

class Transaction:
	"""
	Descripiton: Class to manage transaction between 2 wallets.
	"""
	def __init__(self, sender, receiver, amount, transaction_inputs):
		"""
		Descripiton: Creates a new transaction, used to transfer funds from one
		wallet to another.

		Arguments:
		sender: The public key for the sender.
		receiver: The public key for the receiver of funds.
		amount: The amount to be debited from the sender's wallet.
		transaction_inputs: List of all unspent inputs from the sender wallet.

		Returns:
		An instance of the Transaction class.
		"""

		self.sender = sender
		self.receiver = receiver

		# unicode representation for public/private key
		self.__senderVal = sender.exportKey()
		self.__receiverVal = receiver.exportKey()

		self.transaction_inputs = transaction_inputs
		self.amount = amount
		self.transaction_outputs = []
		self.transaction_id = None

	def gen_signature(self, private_key):
		"""
		Description: Generates a new signature using the private key which
		can be used later for verification during transaction.

		Arguments:
		private_key: The private key of the user who is initiating the transaction.
		"""

		data = self.__senderVal + self.__receiverVal + str(self.amount).encode('ascii')
		data = base64.b64encode(data)

		self.digest = SHA256.new()
		self.digest.update(data)

		signer = PKCS1_v1_5.new(private_key)
		self.signature = signer.sign(self.digest)

	def verify_signature(self):
		"""
		Description: Verifies the signature generated using the sender's public key.

		Returns:
		True if verified correctly else false.
		"""
		verifier = PKCS1_v1_5.new(self.sender)
		verified = verifier.verify(self.digest, self.signature)
		return verified

	def process_transaction(self):
		if not self.verify_signature():
			print('Error while processing transaction')
			return False

		for transaction in self.transaction_inputs:
			transaction.UTXO = BlockChain.UTXOs[transaction.transaction_id]

		# Stop if transaction is too small.
		if self.get_inputs_value() < BlockChain.min_transaction:
			print('Transaction value too small')
			return False

		left_over = self.get_inputs_value() - self.amount # balance in sender's wallet
		self.transaction_id = self.get_transaction_id()

		self.transaction_outputs.append(TransactionOutput(self.receiver, self.amount, self.transaction_id ))
		self.transaction_outputs.append(TransactionOutput(self.sender, left_over, self.transaction_id))

		for transaction in self.transaction_outputs:
			BlockChain.UTXOs[transaction.id] = transaction

		for transaction in self.transaction_inputs:
			if transaction.UTXO is None:
				continue

			del BlockChain.UTXOs[transaction.UTXO.id]

		return True

	def get_transaction_id(self):
		"""
		Description: Gets the id for the current transaction.

		Returns:
		The transaction id.
		"""
		if self.transaction_id is not None: # id is already generated
			return self.transaction_id

		data = self.__senderVal + self.__receiverVal + str(self.amount).encode('ascii')
		data += str(time.time()).encode('ascii') 

		digest = SHA256.new()
		digest.update(data)
		return digest.hexdigest()


	def get_inputs_value(self):
		"""
		Description: Gets the total unspent amount in transaction input

		Returns:
		The total unspent amount.
		"""
		total = 0
		for transaction in self.transaction_inputs:
			if transaction.UTXO is None:
				continue
			total += transaction.UTXO.amount

		return total