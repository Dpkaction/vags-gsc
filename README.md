# GSC Coin - Professional Cryptocurrency Wallet

A complete cryptocurrency implementation featuring a custom blockchain, professional wallet interface, and advanced functionality.

## Features

### Core Blockchain
- **Complete Custom Blockchain**: GSC blockchain with proof-of-work mining
- **21.75 Trillion GSC Supply**: Fixed total supply with halving rewards
- **Mining System**: Built-in mining with locked difficulty at 4
- **Transaction System**: Send and receive GSC with fee calculation
- **Address Generation**: Secure GSC1... format with checksum validation

### Professional Wallet Interface
- **Modern GUI**: Professional Tkinter-based interface
- **Multi-Wallet Support**: Create, encrypt, and manage multiple wallets
- **QR Code Generation**: Generate QR codes for addresses and transactions
- **Paper Wallet Support**: Create secure offline wallets
- **Blockchain Explorer**: View blocks, transactions, and balances

### Security Features
- **Wallet Encryption**: Password-protected wallet files
- **Secure Key Generation**: Cryptographically secure private keys
- **Address Validation**: Checksum validation for all addresses
- **Transaction Verification**: Complete blockchain validation

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Quick Start
```bash
# Clone the repository
git clone https://github.com/your-username/gsc-coin.git
cd gsc-coin

# Install dependencies
pip install -r requirements.txt
python launch_gsc_coin.py
```

The launcher will automatically:
- Check and install required dependencies
- Initialize the GSC blockchain with Genesis block
- Launch the GUI wallet interface

## 📱 Using the GSC Coin Wallet

### 1. Wallet Tab 💰
- **View Balance**: See your current GSC coin balance
- **Send Transactions**: Send GSC coins to other addresses
- **Transaction History**: View all your transactions

### 2. Mining Tab ⛏️
- **Start Mining**: Click "Start Mining" to mine new blocks
- **Adjust Difficulty**: Set mining difficulty (1-8)
- **Monitor Progress**: Watch nonce, hash rate, and current hash
- **Block Details**: View complete block information being mined

### 3. Mempool Tab 📋
- **Pending Transactions**: View all unconfirmed transactions
- **Mempool Statistics**: See total pending transactions and fees
- **Transaction Details**: Inspect individual pending transactions

### 4. Blockchain Tab 🔗
- **Block Explorer**: Browse all blocks in the chain
- **Block Details**: Double-click any block to view full details
- **Chain Statistics**: View blockchain health and statistics

### 5. Network Tab 🌐
- **Save/Load**: Persist blockchain data to disk
- **Validate Chain**: Verify blockchain integrity
- **Network Info**: View complete network statistics

## 🔧 Mining Your GSC Coins

### How to Mine
1. **Add Transactions**: Create transactions in the Wallet tab
2. **Go to Mining Tab**: Switch to the Mining tab
3. **Set Difficulty**: Choose difficulty level (start with 2-3)
4. **Start Mining**: Click "Start Mining" button
5. **Watch Progress**: Monitor nonce, hash rate, and block details
6. **Earn Rewards**: Receive 50 GSC coins per mined block

### Mining Process
- **Nonce Calculation**: The system tries different nonce values
- **Hash Verification**: Each hash must start with required zeros
- **Block Creation**: Successful mining creates a new block
- **Reward Distribution**: Miner receives coinbase transaction
- **Chain Update**: New block is added to the blockchain

## 💡 Understanding GSC Blockchain

### Block Structure
```
Block {
  Index: Block number (0, 1, 2, ...)
  Timestamp: When block was created
  Transactions: List of transactions in block
  Previous Hash: Hash of previous block
  Nonce: Proof of work number
  Hash: Block's unique identifier
  Merkle Root: Transaction verification hash
  Difficulty: Mining difficulty level
  Miner: Address that mined the block
  Reward: Mining reward amount
}
```

### Transaction Structure
```
Transaction {
  Sender: Sending address
  Receiver: Receiving address
  Amount: GSC coins to transfer
  Fee: Transaction fee for miner
  Timestamp: When transaction was created
  TX ID: Unique transaction identifier
  Signature: Transaction signature (future)
}
```

## 🔒 Security Features

- **Hash-based Security**: SHA-256 cryptographic hashing
- **Merkle Tree Verification**: Transaction integrity validation
- **Balance Verification**: Prevents double-spending
- **Chain Validation**: Complete blockchain integrity checks
- **Nonce Proof of Work**: Prevents blockchain manipulation

## 📊 Technical Specifications

- **Hashing Algorithm**: SHA-256
- **Block Time**: Variable (depends on difficulty)
- **Mining Reward**: 50 GSC coins per block
- **Max Transactions per Block**: 10 transactions
- **Difficulty Range**: 1-8 (adjustable)
- **Address Format**: String-based addresses

## 🛠️ Customization

### Modify Mining Reward
Edit `blockchain.py`:
```python
self.mining_reward = 50.0  # Change to desired reward
```

### Adjust Block Size
Edit `blockchain.py`:
```python
selected_transactions = self.mempool[:10]  # Change 10 to desired size
```

### Change Difficulty
Use the GUI difficulty spinner or edit:
```python
self.difficulty = 4  # Change default difficulty
```

## 📁 File Structure

```
GSC-Blockchain-Custom/
├── blockchain.py          # Core blockchain implementation
├── gsc_wallet_gui.py     # GUI wallet application
├── launch_gsc_coin.py    # Launcher script
├── requirements.txt      # Python dependencies
├── README.md            # This file
└── gsc_blockchain.json  # Blockchain data (created after first run)
```

## 🎯 Next Steps

1. **Mine Your First Block**: Start mining to earn GSC coins
2. **Create Transactions**: Send coins between addresses
3. **Explore Blockchain**: Use the blockchain explorer
4. **Customize Settings**: Adjust difficulty and rewards
5. **Network Integration**: Extend for multi-node networking

## 🔮 Future Enhancements

- **Network Protocol**: P2P node communication
- **Digital Signatures**: ECDSA transaction signing
- **Smart Contracts**: Programmable transactions
- **Mobile Wallet**: Mobile app interface
- **Exchange Integration**: Trading functionality

---

**GSC Coin - Your Custom Cryptocurrency Blockchain**
*Built from scratch with complete mining and wallet functionality*
