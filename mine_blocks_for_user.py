"""
GSC Coin - Mine First 5 Blocks for User
Mines blocks and sends rewards to specified wallet address
"""

import sys
import os
import time
from blockchain import GSCBlockchain, Transaction

def mine_blocks_for_user():
    """Mine first 5 blocks for user wallet"""
    
    # User's wallet address
    user_address = "GSC1RwH7jFlpNMp2okBKeMyXxqG8bpx8BUEl"
    
    print("=" * 60)
    print("🪙 GSC COIN - MINING FIRST 5 BLOCKS FOR USER")
    print("=" * 60)
    print(f"Mining rewards will go to: {user_address}")
    print()
    
    # Initialize blockchain
    blockchain = GSCBlockchain()
    
    print(f"Genesis block created. Current blocks: {len(blockchain.chain)}")
    print(f"Starting mining process...")
    print()
    
    # Create some dummy transactions to mine
    dummy_transactions = [
        Transaction(
            sender="GSC_FOUNDATION_RESERVE",
            receiver=user_address,
            amount=100.0,
            fee=1.0,
            timestamp=time.time()
        ),
        Transaction(
            sender="GSC_FOUNDATION_RESERVE", 
            receiver="GSC1TestAddress1",
            amount=50.0,
            fee=0.5,
            timestamp=time.time()
        ),
        Transaction(
            sender="GSC_FOUNDATION_RESERVE",
            receiver="GSC1TestAddress2", 
            amount=25.0,
            fee=0.25,
            timestamp=time.time()
        )
    ]
    
    # Add transactions to mempool
    for tx in dummy_transactions:
        blockchain.mempool.append(tx)
        print(f"Added transaction to mempool: {tx.sender} -> {tx.receiver}: {tx.amount} GSC")
    
    print(f"\nMempool size: {len(blockchain.mempool)} transactions")
    print()
    
    # Mine 5 blocks
    for block_num in range(1, 6):
        print(f"🔨 Mining Block {block_num}/5...")
        print(f"Miner Address: {user_address}")
        
        # Create new block
        latest_block = blockchain.get_latest_block()
        
        # Get current reward (Bitcoin-like halving)
        current_reward = blockchain.get_current_reward()
        
        # Select transactions from mempool (up to 3 per block)
        selected_transactions = blockchain.mempool[:3].copy() if blockchain.mempool else []
        
        # Create block
        from blockchain import Block
        new_block = Block(
            index=latest_block.index + 1,
            timestamp=time.time(),
            transactions=selected_transactions,
            previous_hash=latest_block.hash,
            difficulty=blockchain.difficulty,
            reward=current_reward
        )
        
        # Mine the block
        print(f"Mining with difficulty {blockchain.difficulty}...")
        start_time = time.time()
        
        mining_stats = new_block.mine_block(blockchain.difficulty, user_address)
        
        mining_time = time.time() - start_time
        
        # Add block to chain
        if blockchain.add_block(new_block):
            # Remove mined transactions from mempool
            for tx in selected_transactions:
                if tx in blockchain.mempool:
                    blockchain.mempool.remove(tx)
            
            print(f"✅ Block {new_block.index} mined successfully!")
            print(f"   Hash: {new_block.hash}")
            print(f"   Nonce: {new_block.nonce:,}")
            print(f"   Mining Time: {mining_time:.2f} seconds")
            print(f"   Reward: {current_reward} GSC")
            print(f"   Transactions: {len(new_block.transactions)}")
            
            # Update blockchain height for reward calculation
            blockchain.block_height = new_block.index
            
            print()
        else:
            print(f"❌ Failed to add block {block_num} to chain")
            break
    
    # Show final results
    print("=" * 60)
    print("🎉 MINING COMPLETE!")
    print("=" * 60)
    
    user_balance = blockchain.get_balance(user_address)
    print(f"Your wallet balance: {user_balance:.8f} GSC")
    print(f"Total blocks mined: {len(blockchain.chain) - 1}")  # Exclude genesis
    print(f"Blockchain height: {len(blockchain.chain) - 1}")
    
    # Show all balances
    print("\n📊 All Address Balances:")
    for address, balance in blockchain.balances.items():
        if balance > 0:
            print(f"   {address}: {balance:.8f} GSC")
    
    # Save blockchain
    try:
        blockchain.save_blockchain("gsc_blockchain.json")
        print(f"\n💾 Blockchain saved to gsc_blockchain.json")
    except Exception as e:
        print(f"\n❌ Failed to save blockchain: {e}")
    
    print(f"\n🚀 You can now use your GSC coins in the wallet!")
    print(f"Your address: {user_address}")
    print(f"Your balance: {user_balance:.8f} GSC")

if __name__ == "__main__":
    mine_blocks_for_user()
