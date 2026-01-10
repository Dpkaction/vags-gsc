import hashlib
import json
import time
from datetime import datetime
import threading
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
import pickle

@dataclass
class Transaction:
    """GSC Coin Transaction Class"""
    sender: str
    receiver: str
    amount: float
    fee: float
    timestamp: float
    signature: str = ""
    tx_id: str = ""
    
    def __post_init__(self):
        if not self.tx_id:
            self.tx_id = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """Calculate transaction hash"""
        tx_string = f"{self.sender}{self.receiver}{self.amount}{self.fee}{self.timestamp}"
        return hashlib.sha256(tx_string.encode()).hexdigest()
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def is_valid(self) -> bool:
        """Validate transaction"""
        if self.amount <= 0:
            return False
        if self.fee < 0:
            return False
        if self.sender == self.receiver:
            return False
        return True

@dataclass
class Block:
    """GSC Coin Block Class"""
    index: int
    timestamp: float
    transactions: List[Transaction]
    previous_hash: str
    nonce: int = 0
    hash: str = ""
    merkle_root: str = ""
    difficulty: int = 4
    miner: str = ""
    reward: float = 50.0
    
    def __post_init__(self):
        if not self.merkle_root:
            self.merkle_root = self.calculate_merkle_root()
        if not self.hash:
            self.hash = self.calculate_hash()
    
    def calculate_hash(self) -> str:
        """Calculate block hash"""
        block_string = f"{self.index}{self.timestamp}{self.previous_hash}{self.merkle_root}{self.nonce}{self.difficulty}"
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def calculate_merkle_root(self) -> str:
        """Calculate Merkle root of transactions"""
        if not self.transactions:
            return hashlib.sha256(b"").hexdigest()
        
        tx_hashes = [tx.tx_id for tx in self.transactions]
        
        while len(tx_hashes) > 1:
            if len(tx_hashes) % 2 != 0:
                tx_hashes.append(tx_hashes[-1])
            
            new_hashes = []
            for i in range(0, len(tx_hashes), 2):
                combined = tx_hashes[i] + tx_hashes[i + 1]
                new_hashes.append(hashlib.sha256(combined.encode()).hexdigest())
            
            tx_hashes = new_hashes
        
        return tx_hashes[0]
    
    def mine_block(self, difficulty: int, miner_address: str, callback=None) -> dict:
        """Mine the block with proof of work"""
        target = "0" * difficulty
        mining_stats = {
            'start_time': time.time(),
            'nonce': 0,
            'hash_rate': 0,
            'found': False
        }
        
        self.difficulty = difficulty
        self.miner = miner_address
        
        # Add coinbase transaction (mining reward)
        coinbase_tx = Transaction(
            sender="COINBASE",
            receiver=miner_address,
            amount=self.reward,
            fee=0.0,
            timestamp=time.time()
        )
        self.transactions.insert(0, coinbase_tx)
        self.merkle_root = self.calculate_merkle_root()
        
        print(f"Mining GSC block {self.index} with difficulty {difficulty}...")
        
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.calculate_hash()
            mining_stats['nonce'] = self.nonce
            
            # Calculate hash rate every 1000 nonces
            if self.nonce % 1000 == 0:
                elapsed = time.time() - mining_stats['start_time']
                if elapsed > 0:
                    mining_stats['hash_rate'] = self.nonce / elapsed
                
                if callback:
                    callback(mining_stats)
        
        mining_stats['found'] = True
        mining_stats['final_time'] = time.time() - mining_stats['start_time']
        
        print(f"Block {self.index} mined! Hash: {self.hash}")
        print(f"Nonce: {self.nonce}, Time: {mining_stats['final_time']:.2f}s")
        
        return mining_stats
    
    def is_valid(self, previous_block=None) -> bool:
        """Validate block"""
        # Check hash
        if self.hash != self.calculate_hash():
            return False
        
        # Check previous hash
        if previous_block and self.previous_hash != previous_block.hash:
            return False
        
        # Check merkle root
        if self.merkle_root != self.calculate_merkle_root():
            return False
        
        # Check proof of work
        if not self.hash.startswith("0" * self.difficulty):
            return False
        
        # Validate transactions
        for tx in self.transactions:
            if not tx.is_valid():
                return False
        
        return True
    
    def to_dict(self) -> dict:
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'transactions': [tx.to_dict() for tx in self.transactions],
            'previous_hash': self.previous_hash,
            'nonce': self.nonce,
            'hash': self.hash,
            'merkle_root': self.merkle_root,
            'difficulty': self.difficulty,
            'miner': self.miner,
            'reward': self.reward
        }

class GSCBlockchain:
    """GSC Coin Blockchain Implementation"""
    
    def __init__(self):
        # Initialize basic attributes first
        self.difficulty = 4
        self.difficulty_locked = True
        self.mempool = []
        self.balances = {}
        self.mining_reward = 50.0
        self.is_mining = False
        self.mining_stats = {}
        self.network_node = None
        self.block_height = 0
        self.nodes = []  # Initialize nodes list for network connectivity
        
        # Bitcoin-like reward system
        self.initial_reward = 50.0  # Starting reward like Bitcoin
        self.halving_interval = 210000  # Halving every 210,000 blocks like Bitcoin
        self.max_supply = 21750000000000  # 21.75 trillion GSC
        self.current_supply = 0
        
        # Initialize empty chain first
        self.chain = []
        
        # Create and add genesis block
        genesis_block = self.create_genesis_block()
    
    def get_current_reward(self):
        """Calculate current mining reward based on Bitcoin-like halving"""
        halvings = self.block_height // self.halving_interval
        if halvings >= 64:  # After 64 halvings, reward becomes 0
            return 0
        return self.initial_reward / (2 ** halvings)
    
    def create_genesis_block(self):
        print("Creating GSC Coin Genesis Block...")
        print(f"Total Supply: {self.max_supply:,.0f} GSC (21.75 Trillion)")
        
        # Genesis block with foundation allocation (not for user wallets)
        genesis_transactions = [
            Transaction(
                sender="Genesis",
                receiver="GSC_FOUNDATION_RESERVE",  # Foundation reserve, not user accessible
                amount=self.max_supply,  # Exactly 21.75 trillion supply
                fee=0,
                timestamp=1704067200  # Fixed genesis timestamp (Jan 1, 2024)
            )
        ]
        
        genesis_block = Block(
            index=0,
            transactions=genesis_transactions,
            timestamp=1704067200,  # Fixed genesis timestamp (Jan 1, 2024)
            previous_hash="0" * 64,
            nonce=0
        )
        
        # Mine genesis block
        genesis_block.mine_block(1, "GSC_FOUNDATION")
        self.chain.append(genesis_block)
        
        # Update balances
        self.update_balances()
        
        self.current_supply = 21750000000000  # Set current supply to max
        print(f"GSC Coin Genesis Block Created!")
        print(f"Genesis Hash: {genesis_block.hash}")
        print(f"Total Supply: {self.current_supply:,.0f} GSC")
        print(f"Foundation Reserve: GSC_FOUNDATION_RESERVE")
        print(f"User wallets start with 0 GSC - must mine or receive coins")
        
        return genesis_block
    
    def get_latest_block(self) -> Block:
        """Get the latest block in the chain"""
        return self.chain[-1]
    
    def add_transaction_to_mempool(self, transaction: Transaction) -> bool:
        """Add transaction to mempool with Bitcoin-like validation"""
        if not self.is_transaction_valid(transaction):
            return False
            
        # Check if sender has sufficient balance
        sender_balance = self.get_balance(transaction.sender)
        if sender_balance >= (transaction.amount + transaction.fee):
            # Check if transaction already exists in mempool
            if not any(tx.tx_id == transaction.tx_id for tx in self.mempool):
                self.mempool.append(transaction)
                print(f"Transaction added to mempool: {transaction.tx_id[:16]}...")
                
                # Broadcast to network
                self.broadcast_new_transaction(transaction)
                return True
            else:
                print(f"Transaction already in mempool: {transaction.tx_id[:16]}...")
                return False
        else:
            print(f"Insufficient balance for transaction: {transaction.tx_id[:16]}...")
            return False
    
    def is_transaction_valid(self, transaction: Transaction) -> bool:
        """Bitcoin-like transaction validation"""
        # Basic validation
        if not transaction.is_valid():
            return False
            
        # Check for double spending in mempool
        for tx in self.mempool:
            if tx.sender == transaction.sender and tx.tx_id != transaction.tx_id:
                sender_balance = self.get_balance(transaction.sender)
                total_spending = sum(t.amount + t.fee for t in self.mempool if t.sender == transaction.sender)
                total_spending += transaction.amount + transaction.fee
                if total_spending > sender_balance:
                    print(f"Double spending detected: {transaction.tx_id[:16]}...")
                    return False
        
        return True
    
    def create_new_block(self, miner_address: str) -> Block:
        """Create a new block with transactions from mempool"""
        latest_block = self.get_latest_block()
        
        # Select transactions from mempool (up to 10 transactions per block)
        selected_transactions = self.mempool[:10].copy()
        
        # Get current reward based on Bitcoin-like halving
        current_reward = self.get_current_reward()
        
        new_block = Block(
            index=latest_block.index + 1,
            timestamp=time.time(),
            transactions=selected_transactions,
            previous_hash=latest_block.hash,
            difficulty=4,  # LOCKED at 4 - never changes
            reward=current_reward
        )
        
        return new_block
    
    def mine_pending_transactions(self, miner_address: str, callback=None) -> Block:
        """Mine pending transactions with Bitcoin-like mining process"""
        if self.is_mining:
            print("Mining already in progress...")
            return None
        
        self.is_mining = True
        
        try:
            # Create new block
            new_block = self.create_new_block(miner_address)
            self.current_mining_block = new_block  # Store for GUI updates
            
            # Mine the block with Bitcoin-like proof of work
            mining_stats = new_block.mine_block(self.difficulty, miner_address, callback)
            
            # Add block to chain
            if self.add_block(new_block):
                # Remove mined transactions from mempool
                for tx in new_block.transactions[1:]:  # Skip coinbase transaction
                    if tx in self.mempool:
                        self.mempool.remove(tx)
                
                self.mining_stats = mining_stats
                self.block_height = len(self.chain) - 1
                
                # Broadcast new block to network
                self.broadcast_new_block(new_block)
                
                print(f"Block {new_block.index} successfully mined and added to GSC blockchain!")
                print(f"Block Hash: {new_block.hash}")
                print(f"Mining Reward: {new_block.reward} GSC")
                print(f"Network Height: {self.block_height}")
                
                return new_block
            else:
                print("Failed to add mined block to chain!")
                return None
        
        finally:
            self.is_mining = False
            if hasattr(self, 'current_mining_block'):
                delattr(self, 'current_mining_block')
    
    def add_block(self, block: Block) -> bool:
        """Add a new block to the chain"""
        previous_block = self.get_latest_block()
        
        if block.is_valid(previous_block):
            self.chain.append(block)
            self.update_balances()
            return True
        
        return False
    
    def update_balances(self):
        """Update all account balances"""
        self.balances.clear()
        
        for block in self.chain:
            for tx in block.transactions:
                # Deduct from sender (except for coinbase and genesis)
                if tx.sender not in ["COINBASE", "GENESIS"]:
                    if tx.sender not in self.balances:
                        self.balances[tx.sender] = 0.0
                    self.balances[tx.sender] -= (tx.amount + tx.fee)
                
                # Add to receiver
                if tx.receiver not in self.balances:
                    self.balances[tx.receiver] = 0.0
                self.balances[tx.receiver] += tx.amount
                
                # Add fee to miner (if not coinbase transaction)
                if tx.sender != "COINBASE" and block.miner:
                    if block.miner not in self.balances:
                        self.balances[block.miner] = 0.0
                    self.balances[block.miner] += tx.fee
    
    def get_balance(self, address: str) -> float:
        """Get balance for an address"""
        return self.balances.get(address, 0.0)
    
    def is_chain_valid(self) -> bool:
        """Bitcoin-like blockchain validation"""
        if len(self.chain) == 0:
            return False
        
        # Validate genesis block
        genesis = self.chain[0]
        if genesis.index != 0 or genesis.previous_hash != "0" * 64:
            print("Invalid genesis block")
            return False
        
        # Validate each block in sequence
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            # Bitcoin-like validation checks
            if not self.validate_block_bitcoin_style(current_block, previous_block):
                print(f"Block {i} failed Bitcoin-style validation")
                return False
        
        # Validate balances consistency
        if not self.validate_balances():
            print("Balance validation failed")
            return False
        
        print("Blockchain validation passed - Bitcoin-like standards met")
        return True
    
    def is_chain_valid_network(self, chain) -> bool:
        """Validate a chain received from network"""
        if len(chain) == 0:
            return False
        
        # Validate genesis block
        genesis = chain[0]
        if genesis.index != 0 or genesis.previous_hash != "0" * 64:
            return False
        
        # Validate each block in sequence
        for i in range(1, len(chain)):
            current_block = chain[i]
            previous_block = chain[i - 1]
            
            if not current_block.is_valid(previous_block):
                return False
        
        return True
    
    def replace_chain_if_longer(self, new_chain):
        """Replace current chain if new chain is longer and valid"""
        if len(new_chain) > len(self.chain) and self.is_chain_valid_network(new_chain):
            print(f"Replacing chain with longer valid chain ({len(new_chain)} blocks)")
            self.chain = new_chain
            self.update_balances()
            return True
        return False
    
    def set_network_node(self, network_node):
        """Set network node for P2P communication"""
        self.network_node = network_node
    
    def broadcast_new_block(self, block):
        """Broadcast new block to network"""
        if self.network_node:
            self.network_node.broadcast_block(block)
    
    def broadcast_new_transaction(self, transaction):
        """Broadcast new transaction to network"""
        if self.network_node:
            self.network_node.broadcast_transaction(transaction)
    
    def is_block_valid(self, block, previous_block):
        """Check if a single block is valid"""
        return block.is_valid(previous_block)
    
    def validate_block_bitcoin_style(self, block: Block, previous_block: Block) -> bool:
        """Bitcoin-style block validation"""
        
        # 1. Check block index sequence
        if block.index != previous_block.index + 1:
            print(f"Invalid block index: {block.index}, expected: {previous_block.index + 1}")
            return False
        
        # 2. Check previous hash linkage
        if block.previous_hash != previous_block.hash:
            print(f"Invalid previous hash linkage")
            return False
        
        # 3. Check block hash integrity
        if block.hash != block.calculate_hash():
            print(f"Block hash integrity check failed")
            return False
        
        # 4. Check proof of work (difficulty requirement)
        if not block.hash.startswith("0" * self.difficulty):
            print(f"Proof of work validation failed - difficulty {self.difficulty}")
            return False
        
        # 5. Check merkle root
        if block.merkle_root != block.calculate_merkle_root():
            print(f"Merkle root validation failed")
            return False
        
        # 6. Validate all transactions in block
        for i, tx in enumerate(block.transactions):
            if not self.validate_transaction_bitcoin_style(tx, block, i):
                print(f"Transaction {i} validation failed")
                return False
        
        # 7. Check coinbase transaction (first transaction must be coinbase)
        if len(block.transactions) > 0:
            coinbase = block.transactions[0]
            if coinbase.sender != "COINBASE":
                print("First transaction must be coinbase")
                return False
            
            # Check mining reward amount
            expected_reward = self.get_current_reward()
            if coinbase.amount != expected_reward:
                print(f"Invalid mining reward: {coinbase.amount}, expected: {expected_reward}")
                return False
        
        # 8. Check timestamp (must be greater than previous block)
        if block.timestamp <= previous_block.timestamp:
            print("Block timestamp must be greater than previous block")
            return False
        
        return True
    
    def validate_transaction_bitcoin_style(self, tx: Transaction, block: Block, tx_index: int) -> bool:
        """Bitcoin-style transaction validation"""
        
        # Skip coinbase transaction validation (different rules)
        if tx.sender == "COINBASE":
            return True
        
        # 1. Check transaction hash integrity
        if tx.tx_id != tx.calculate_hash():
            print(f"Transaction hash integrity failed")
            return False
        
        # 2. Check basic transaction validity
        if not tx.is_valid():
            print(f"Basic transaction validation failed")
            return False
        
        # 3. Check sender has sufficient balance (at time of transaction)
        sender_balance = self.get_balance_at_block(tx.sender, block.index - 1)
        if sender_balance < (tx.amount + tx.fee):
            print(f"Insufficient balance: {sender_balance} < {tx.amount + tx.fee}")
            return False
        
        # 4. Check for double spending
        if self.check_double_spending(tx, block.index):
            print(f"Double spending detected")
            return False
        
        return True
    
    def validate_balances(self) -> bool:
        """Validate that all balances are consistent with blockchain history"""
        calculated_balances = {}
        
        # Recalculate balances from scratch
        for block in self.chain:
            for tx in block.transactions:
                # Handle coinbase transactions
                if tx.sender == "COINBASE":
                    if tx.receiver not in calculated_balances:
                        calculated_balances[tx.receiver] = 0.0
                    calculated_balances[tx.receiver] += tx.amount
                
                # Handle genesis transactions
                elif tx.sender == "Genesis":
                    if tx.receiver not in calculated_balances:
                        calculated_balances[tx.receiver] = 0.0
                    calculated_balances[tx.receiver] += tx.amount
                
                # Handle regular transactions
                else:
                    # Deduct from sender
                    if tx.sender not in calculated_balances:
                        calculated_balances[tx.sender] = 0.0
                    calculated_balances[tx.sender] -= (tx.amount + tx.fee)
                    
                    # Add to receiver
                    if tx.receiver not in calculated_balances:
                        calculated_balances[tx.receiver] = 0.0
                    calculated_balances[tx.receiver] += tx.amount
                    
                    # Add fee to miner
                    if block.miner and block.miner not in calculated_balances:
                        calculated_balances[block.miner] = 0.0
                    if block.miner:
                        calculated_balances[block.miner] += tx.fee
        
        # Compare with current balances and update if needed
        for address, balance in calculated_balances.items():
            if abs(self.balances.get(address, 0.0) - balance) > 0.00000001:  # Allow for floating point precision
                print(f"Balance mismatch for {address}: stored={self.balances.get(address, 0.0)}, calculated={balance}")
                # Update the stored balance to match calculated balance
                self.balances[address] = balance
        
        # Also ensure all calculated balances are in the stored balances
        self.balances = calculated_balances.copy()
        
        return True
    
    def get_balance_at_block(self, address: str, block_index: int) -> float:
        """Get balance of address at specific block height"""
        balance = 0.0
        
        for i in range(min(block_index + 1, len(self.chain))):
            block = self.chain[i]
            for tx in block.transactions:
                if tx.sender == address and tx.sender not in ["COINBASE", "Genesis"]:
                    balance -= (tx.amount + tx.fee)
                if tx.receiver == address:
                    balance += tx.amount
                if block.miner == address and tx.sender not in ["COINBASE", "Genesis"]:
                    balance += tx.fee
        
        return balance
    
    def check_double_spending(self, transaction: Transaction, current_block_index: int) -> bool:
        """Check if transaction represents double spending"""
        # Look for identical transactions in previous blocks
        for i in range(current_block_index):
            if i < len(self.chain):
                block = self.chain[i]
                for tx in block.transactions:
                    if (tx.sender == transaction.sender and 
                        tx.receiver == transaction.receiver and 
                        tx.amount == transaction.amount and
                        tx.timestamp == transaction.timestamp):
                        return True
        return False
    
    def get_blockchain_info(self) -> dict:
        """Get blockchain information"""
        return {
            'blocks': len(self.chain),
            'difficulty': self.difficulty,
            'mempool_size': len(self.mempool),
            'total_addresses': len(self.balances),
            'is_mining': self.is_mining,
            'latest_block_hash': self.get_latest_block().hash,
            'chain_valid': self.is_chain_valid()
        }
    
    def save_blockchain(self, filename: str):
        """Save blockchain to file"""
        blockchain_data = {
            'chain': [block.to_dict() for block in self.chain],
            'mempool': [tx.to_dict() for tx in self.mempool],
            'balances': self.balances,
            'difficulty': self.difficulty,
            'mining_reward': self.mining_reward
        }
        
        with open(filename, 'w') as f:
            json.dump(blockchain_data, f, indent=2)
        
        print(f"GSC Blockchain saved to {filename}")
    
    def load_blockchain(self, filename: str):
        """Load blockchain from file"""
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            
            # Reconstruct blockchain
            self.chain.clear()
            for block_data in data['chain']:
                transactions = [
                    Transaction(**tx_data) for tx_data in block_data['transactions']
                ]
                block = Block(
                    index=block_data['index'],
                    timestamp=block_data['timestamp'],
                    transactions=transactions,
                    previous_hash=block_data['previous_hash'],
                    nonce=block_data['nonce'],
                    hash=block_data['hash'],
                    merkle_root=block_data['merkle_root'],
                    difficulty=block_data['difficulty'],
                    miner=block_data['miner'],
                    reward=block_data['reward']
                )
                self.chain.append(block)
            
            # Reconstruct mempool
            self.mempool = [Transaction(**tx_data) for tx_data in data['mempool']]
            
            # Restore other data
            self.balances = data['balances']
            self.difficulty = data['difficulty']
            self.mining_reward = data['mining_reward']
            
            print(f"GSC Blockchain loaded from {filename}")
            
        except FileNotFoundError:
            print(f"Blockchain file {filename} not found. Starting with genesis block.")
            self.create_genesis_block()
        except Exception as e:
            print(f"Error loading blockchain: {e}")
            self.create_genesis_block()

# Example usage and testing
if __name__ == "__main__":
    # Create GSC blockchain
    gsc = GSCBlockchain()
    
    print("=== GSC Coin Blockchain Started ===")
    print(f"Genesis block created with hash: {gsc.chain[0].hash}")
    print(f"GSC Foundation balance: {gsc.get_balance('GSC_FOUNDATION')}")
    
    # Create some test transactions
    tx1 = Transaction("GSC_FOUNDATION", "Alice", 100.0, 1.0, time.time())
    tx2 = Transaction("GSC_FOUNDATION", "Bob", 200.0, 2.0, time.time())
    
    # Add to mempool
    gsc.add_transaction_to_mempool(tx1)
    gsc.add_transaction_to_mempool(tx2)
    
    print(f"\nMempool size: {len(gsc.mempool)}")
    
    # Mine a block
    print("\n=== Mining Block 1 ===")
    mined_block = gsc.mine_pending_transactions("Miner1")
    
    if mined_block:
        print(f"Block 1 mined successfully!")
        print(f"Block hash: {mined_block.hash}")
        print(f"Nonce: {mined_block.nonce}")
        print(f"Transactions in block: {len(mined_block.transactions)}")
        
        # Check balances
        print(f"\nUpdated Balances:")
        for address, balance in gsc.balances.items():
            print(f"{address}: {balance} GSC")
    
    # Blockchain info
    print(f"\n=== GSC Blockchain Info ===")
    info = gsc.get_blockchain_info()
    for key, value in info.items():
        print(f"{key}: {value}")
