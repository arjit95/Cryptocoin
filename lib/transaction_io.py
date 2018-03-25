from Crypto.Hash import SHA256

class TransactionInput:
	def __init__(self, transaction_id):
		self.transaction_id = transaction_id
		self.UTXO = None # contains the transaction output

class TransactionOutput:
	def __init__(self, reciepient, amount, transaction_id):
		self.reciepient = reciepient
		self.amount = amount
		self.transaction_id = transaction_id

		data = reciepient.exportKey() + str(transaction_id).encode('ascii')
		data += str(self.amount).encode('ascii') # prepare data for encryption

		digest = SHA256.new()
		digest.update(data) # encrypt data

		self.id = digest.hexdigest() # store encrypted data

	def is_mine(self, public_key):
		return self.reciepient == public_key