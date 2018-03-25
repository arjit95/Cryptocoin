import time
from Crypto.Hash import SHA256

class BlockChain:
	UTXOs = {} #list of all unspent transactions.
	min_transaction = 0.1
	difficulty = 1

	def __init__(self):
		self.__blocks = []

	def add(self, block):
		"""
		Description: Adds a block to the block chain

		Arguments:
		block: An instance of the block which is to be added to the block chain.
		"""

		# check if block is a valid instance of class Block
		if not isinstance(block, Block):
			raise RuntimeError

		# mine the newly created block
		block.mine()

		#add the block to the block chain
		self.__blocks.append(block)
		print("Block mined at :{0}".format(self.size()))

	def get_block(self, index):
		"""
		Description: Gets a block at the specified index

		Arguments:
		index: The index at which the block is to be fetched

		Returns:
		The block at the specified index from the chain
		"""

		if index >= self.size():
			raise IndexError('The index specified is greater than the blockchain length')

		return self.__blocks[index]

	def size(self):
		"""
		Description: Gets the size of the blockchain

		Returns:
		The length of the blockchain
		"""

		return len(self.__blocks)

	def is_valid(self):
		"""
		Description: Checks if the block chain is valid and is not tampered with.

		Returns:
		True if the block chain is valid
		"""

		if self.size() == 0:
			return True

		target_hash = '0' * BlockChain.difficulty
		for i in range(1, self.size()):
			current_block = self.get_block(i)
			prev_block = self.get_block(i - 1)

			# check if hash is not tampered with. Both computed hash and the current hash should be
			# same.
			if current_block.hash != current_block.calc_hash():
				print('Block #{0} has incorrect hash value {1}'.format(i, current_block.hash))
				return False

			# check if chain link is maintained. Block chain is based on a linked-list concept, so check
			# if the link is maintained between all blocks.
			if current_block.previous_hash != prev_block.hash:
				print('Block #{0} has broken links'.format(i))
				return False

			# check if block is mined or not
			if current_block.hash[0:self.difficulty] != target_hash:
				print('Block #{0} is yet to be mined'.format(i))
				return False

		return True

class Block:
	def __init__(self, previous_hash, nonce=None):
		self.previous_hash = previous_hash
		self.timestamp = time.time()
		self.nonce = nonce or 0 # random value for mining
		self.transactions = []
		self.merkle_root = ""

		self.hash = self.calc_hash()

	def calc_hash(self):
		"""
		Generates a random hash from the available data

		Returns:
		The computed sha256 hash value from the data
		"""
		hash_string = self.previous_hash + str(self.timestamp) + self.merkle_root + str(self.nonce)

		digest = SHA256.new()
		digest.update(hash_string.encode('ascii'))
		return digest.hexdigest()

	def add_transaction(self, transaction):
		"""
		Adds a transaction to the block

		Arguments:
		transaction: Transaction class containing the details of the transaction.

		Returns:
		True if the transaction is successfully added.
		"""

		if not transaction or (self.previous_hash != '0' and not transaction.process_transaction()):
			print('Transaction failed to process. Discarded!!')
			return False

		self.transactions.append(transaction)
		print('Transaction successfully added to block..')
		return True

	def __get_merkle_root(self):
		transactions = self.transactions
		count = len(transactions)

		prev_layer = []

		for transaction in transactions:
			prev_layer.append(transaction.transaction_id)

		tree_layer = prev_layer
		digest = SHA256.new()

		while count > 1:
			tree_layer = []

			for i in range(1, len(prev_layer)):
				digest.update(prev_layer[i - 1] + prev_layer[i])
				tree_layer.append(digest.hexdigest())

			count = len(tree_layer)
			prev_layer = tree_layer

		return tree_layer[0] if len(tree_layer) == 1 else ""

	def mine(self):
		"""
		Once a block is added to the blockchain it needs to be mined. This method is the
		proof of work concept similar to the bitcoin blockchain.

		Eg: If difficulty is set to 2 then:
		target: '00'
		hash: '00....abc' (A sha256 hash value which starts with '00')

		It will continue to find the hash value until it finds a hash which starts with target.
		As more blocks are added to the block chain this difficulty will increase

		Arguments:
		difficulty: The number of consecutive '0' for the generated hash to start with.
		"""
		difficulty = BlockChain.difficulty

		target = '0' * difficulty
		self.merkle_root = self.__get_merkle_root()

		while self.hash[0:difficulty] != target:
			self.nonce += 1
			self.hash = self.calc_hash()

		print('Calculated hash for new block is: {0}'.format(self.hash))