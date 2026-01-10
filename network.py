"""
GSC Coin P2P Network Module
Handles peer-to-peer networking, node discovery, and blockchain synchronization
"""

import socket
import threading
import json
import time
import hashlib
from datetime import datetime
import pickle

class GSCNetworkNode:
    def __init__(self, blockchain, port=8333):
        self.blockchain = blockchain
        self.port = port
        self.peers = set()
        self.server_socket = None
        self.running = False
        self.node_id = self.generate_node_id()
        self.known_nodes = set()
        self.sync_lock = threading.Lock()
        
    def generate_node_id(self):
        """Generate unique node ID"""
        return hashlib.sha256(f"{socket.gethostname()}{time.time()}".encode()).hexdigest()[:16]
    
    def start_server(self):
        """Start P2P server to accept incoming connections"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(('0.0.0.0', self.port))
            self.server_socket.listen(10)
            self.running = True
            
            print(f"GSC Node started on port {self.port}")
            print(f"Node ID: {self.node_id}")
            
            # Start server thread
            server_thread = threading.Thread(target=self.accept_connections)
            server_thread.daemon = True
            server_thread.start()
            
            # Start peer discovery
            discovery_thread = threading.Thread(target=self.discover_peers)
            discovery_thread.daemon = True
            discovery_thread.start()
            
            return True
        except Exception as e:
            print(f"Failed to start P2P server: {e}")
            return False
    
    def accept_connections(self):
        """Accept incoming peer connections"""
        while self.running:
            try:
                client_socket, address = self.server_socket.accept()
                print(f"New peer connected: {address}")
                
                # Handle peer in separate thread
                peer_thread = threading.Thread(
                    target=self.handle_peer, 
                    args=(client_socket, address)
                )
                peer_thread.daemon = True
                peer_thread.start()
                
            except Exception as e:
                if self.running:
                    print(f"Error accepting connection: {e}")
    
    def handle_peer(self, client_socket, address):
        """Handle communication with a peer"""
        peer_address = f"{address[0]}:{address[1]}"
        self.peers.add(peer_address)
        
        try:
            while self.running:
                data = client_socket.recv(4096)
                if not data:
                    break
                
                try:
                    message = json.loads(data.decode())
                    self.process_message(message, client_socket, peer_address)
                except json.JSONDecodeError:
                    continue
                    
        except Exception as e:
            print(f"Error handling peer {peer_address}: {e}")
        finally:
            client_socket.close()
            self.peers.discard(peer_address)
            print(f"Peer disconnected: {peer_address}")
    
    def process_message(self, message, client_socket, peer_address):
        """Process incoming message from peer"""
        msg_type = message.get('type')
        
        if msg_type == 'handshake':
            self.handle_handshake(message, client_socket, peer_address)
        elif msg_type == 'get_blockchain':
            self.send_blockchain(client_socket)
        elif msg_type == 'blockchain':
            self.handle_blockchain_update(message)
        elif msg_type == 'new_block':
            self.handle_new_block(message)
        elif msg_type == 'new_transaction':
            self.handle_new_transaction(message)
        elif msg_type == 'peer_list':
            self.handle_peer_list(message)
        elif msg_type == 'ping':
            self.send_pong(client_socket)
    
    def handle_handshake(self, message, client_socket, peer_address):
        """Handle handshake from new peer"""
        peer_node_id = message.get('node_id')
        peer_chain_length = message.get('chain_length', 0)
        
        # Send our handshake response
        response = {
            'type': 'handshake_response',
            'node_id': self.node_id,
            'chain_length': len(self.blockchain.chain),
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            client_socket.send(json.dumps(response).encode())
        except:
            pass
        
        # If peer has longer chain, request it
        if peer_chain_length > len(self.blockchain.chain):
            self.request_blockchain(client_socket)
    
    def send_blockchain(self, client_socket):
        """Send our blockchain to requesting peer"""
        try:
            blockchain_data = {
                'type': 'blockchain',
                'chain': [self.serialize_block(block) for block in self.blockchain.chain],
                'node_id': self.node_id
            }
            
            data = json.dumps(blockchain_data).encode()
            client_socket.send(data)
        except Exception as e:
            print(f"Error sending blockchain: {e}")
    
    def handle_blockchain_update(self, message):
        """Handle incoming blockchain from peer"""
        with self.sync_lock:
            try:
                peer_chain_data = message.get('chain', [])
                peer_chain = [self.deserialize_block(block_data) for block_data in peer_chain_data]
                
                # Validate and potentially replace our chain
                if self.is_valid_chain(peer_chain) and len(peer_chain) > len(self.blockchain.chain):
                    print(f"Received longer valid chain ({len(peer_chain)} blocks)")
                    self.blockchain.chain = peer_chain
                    self.blockchain.update_balances()
                    print("Blockchain synchronized with network")
                    
            except Exception as e:
                print(f"Error processing blockchain update: {e}")
    
    def handle_new_block(self, message):
        """Handle new block broadcast from peer"""
        try:
            block_data = message.get('block')
            new_block = self.deserialize_block(block_data)
            
            # Validate and add block if valid
            if self.blockchain.is_block_valid(new_block, self.blockchain.chain[-1]):
                self.blockchain.chain.append(new_block)
                self.blockchain.update_balances()
                print(f"New block added from network: {new_block.hash[:16]}...")
                
                # Broadcast to other peers
                self.broadcast_block(new_block, exclude_peer=message.get('sender'))
                
        except Exception as e:
            print(f"Error handling new block: {e}")
    
    def handle_new_transaction(self, message):
        """Handle new transaction broadcast from peer"""
        try:
            tx_data = message.get('transaction')
            
            # Add to mempool if valid and not already present
            tx_id = tx_data.get('tx_id')
            if not any(tx.tx_id == tx_id for tx in self.blockchain.mempool):
                transaction = self.deserialize_transaction(tx_data)
                if self.blockchain.is_transaction_valid(transaction):
                    self.blockchain.mempool.append(transaction)
                    print(f"New transaction added to mempool: {tx_id[:16]}...")
                    
                    # Broadcast to other peers
                    self.broadcast_transaction(transaction, exclude_peer=message.get('sender'))
                    
        except Exception as e:
            print(f"Error handling new transaction: {e}")
    
    def connect_to_peer(self, host, port):
        """Connect to a peer node"""
        try:
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_socket.connect((host, port))
            
            # Send handshake
            handshake = {
                'type': 'handshake',
                'node_id': self.node_id,
                'chain_length': len(self.blockchain.chain),
                'timestamp': datetime.now().isoformat()
            }
            
            peer_socket.send(json.dumps(handshake).encode())
            
            # Handle peer in separate thread
            peer_address = f"{host}:{port}"
            peer_thread = threading.Thread(
                target=self.handle_peer, 
                args=(peer_socket, (host, port))
            )
            peer_thread.daemon = True
            peer_thread.start()
            
            return True
            
        except Exception as e:
            print(f"Failed to connect to peer {host}:{port}: {e}")
            return False
    
    def discover_peers(self):
        """Discover and connect to other GSC nodes"""
        # Enhanced peer discovery with better connectivity
        potential_peers = [
            ('127.0.0.1', 8334),
            ('127.0.0.1', 8335),
            ('127.0.0.1', 8336),
            ('localhost', 8334),
            ('localhost', 8335)
        ]
        
        while self.running:
            for host, port in potential_peers:
                peer_addr = f"{host}:{port}"
                if peer_addr not in self.peers and port != self.port:
                    try:
                        self.connect_to_peer(host, port)
                        time.sleep(1)  # Small delay between connections
                    except:
                        pass
            
            time.sleep(15)  # Check for new peers more frequently
    def try_connect_peer(self, ip, port):
        """Try to connect to a potential peer"""
        try:
            test_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_socket.settimeout(1)
            result = test_socket.connect_ex((ip, port))
            test_socket.close()
            
            if result == 0:  # Connection successful
                peer_address = f"{ip}:{port}"
                if peer_address not in self.peers:
                    self.connect_to_peer(ip, port)
                    
        except:
            pass
    
    def broadcast_block(self, block, exclude_peer=None):
        """Broadcast new block to all peers"""
        message = {
            'type': 'new_block',
            'block': self.serialize_block(block),
            'sender': self.node_id,
            'timestamp': datetime.now().isoformat()
        }
        
        self.broadcast_message(message, exclude_peer)
    
    def broadcast_transaction(self, transaction, exclude_peer=None):
        """Broadcast new transaction to all peers"""
        message = {
            'type': 'new_transaction',
            'transaction': self.serialize_transaction(transaction),
            'sender': self.node_id,
            'timestamp': datetime.now().isoformat()
        }
        
        self.broadcast_message(message, exclude_peer)
    
    def broadcast_message(self, message, exclude_peer=None):
        """Broadcast message to all connected peers"""
        data = json.dumps(message).encode()
        
        for peer_address in list(self.peers):
            if exclude_peer and peer_address == exclude_peer:
                continue
                
            try:
                # This is simplified - in practice you'd maintain persistent connections
                host, port = peer_address.split(':')
                peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                peer_socket.settimeout(5)
                peer_socket.connect((host, int(port)))
                peer_socket.send(data)
                peer_socket.close()
                
            except Exception as e:
                print(f"Failed to broadcast to {peer_address}: {e}")
                self.peers.discard(peer_address)
    
    def serialize_block(self, block):
        """Serialize block for network transmission"""
        return {
            'index': block.index,
            'timestamp': block.timestamp,
            'transactions': [self.serialize_transaction(tx) for tx in block.transactions],
            'previous_hash': block.previous_hash,
            'nonce': block.nonce,
            'hash': block.hash,
            'merkle_root': getattr(block, 'merkle_root', ''),
            'difficulty': getattr(block, 'difficulty', 4),
            'miner': getattr(block, 'miner', ''),
            'reward': getattr(block, 'reward', 0)
        }
    
    def deserialize_block(self, block_data):
        """Deserialize block from network data"""
        from blockchain import Block, Transaction
        
        transactions = [self.deserialize_transaction(tx_data) for tx_data in block_data.get('transactions', [])]
        
        block = Block(
            index=block_data['index'],
            transactions=transactions,
            previous_hash=block_data['previous_hash']
        )
        
        block.timestamp = block_data['timestamp']
        block.nonce = block_data['nonce']
        block.hash = block_data['hash']
        block.merkle_root = block_data.get('merkle_root', '')
        block.difficulty = block_data.get('difficulty', 4)
        block.miner = block_data.get('miner', '')
        block.reward = block_data.get('reward', 0)
        
        return block
    
    def serialize_transaction(self, transaction):
        """Serialize transaction for network transmission"""
        return {
            'sender': transaction.sender,
            'receiver': transaction.receiver,
            'amount': transaction.amount,
            'fee': getattr(transaction, 'fee', 0),
            'timestamp': transaction.timestamp,
            'tx_id': getattr(transaction, 'tx_id', '')
        }
    
    def deserialize_transaction(self, tx_data):
        """Deserialize transaction from network data"""
        from blockchain import Transaction
        
        transaction = Transaction(
            sender=tx_data['sender'],
            receiver=tx_data['receiver'],
            amount=tx_data['amount']
        )
        
        transaction.fee = tx_data.get('fee', 0)
        transaction.timestamp = tx_data['timestamp']
        transaction.tx_id = tx_data.get('tx_id', '')
        
        return transaction
    
    def is_valid_chain(self, chain):
        """Validate a blockchain"""
        try:
            return self.blockchain.is_chain_valid_network(chain)
        except:
            return False
    
    def get_local_ip(self):
        """Get local IP address"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def broadcast_blockchain(self):
        """Broadcast entire blockchain to all connected peers"""
        if not self.peers:
            print("No peers connected to broadcast blockchain")
            return False
        
        try:
            blockchain_data = {
                'type': 'blockchain_broadcast',
                'chain': [self.serialize_block(block) for block in self.blockchain.chain],
                'node_id': self.node_id,
                'timestamp': datetime.now().isoformat(),
                'chain_length': len(self.blockchain.chain)
            }
            
            broadcast_count = 0
            for peer_address in list(self.peers):
                try:
                    host, port = peer_address.split(':')
                    peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    peer_socket.settimeout(10)
                    peer_socket.connect((host, int(port)))
                    
                    data = json.dumps(blockchain_data).encode()
                    peer_socket.send(data)
                    peer_socket.close()
                    broadcast_count += 1
                    print(f"Blockchain broadcasted to {peer_address}")
                    
                except Exception as e:
                    print(f"Failed to broadcast blockchain to {peer_address}: {e}")
                    self.peers.discard(peer_address)
            
            print(f"Blockchain broadcast completed to {broadcast_count} peers")
            return broadcast_count > 0
            
        except Exception as e:
            print(f"Error broadcasting blockchain: {e}")
            return False
    
    def request_blockchain_from_peers(self):
        """Request blockchain from all connected peers"""
        if not self.peers:
            print("No peers connected to request blockchain from")
            return False
        
        request_message = {
            'type': 'get_blockchain',
            'node_id': self.node_id,
            'timestamp': datetime.now().isoformat()
        }
        
        request_count = 0
        for peer_address in list(self.peers):
            try:
                host, port = peer_address.split(':')
                peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                peer_socket.settimeout(5)
                peer_socket.connect((host, int(port)))
                
                data = json.dumps(request_message).encode()
                peer_socket.send(data)
                peer_socket.close()
                request_count += 1
                print(f"Blockchain requested from {peer_address}")
                
            except Exception as e:
                print(f"Failed to request blockchain from {peer_address}: {e}")
                self.peers.discard(peer_address)
        
        print(f"Blockchain requested from {request_count} peers")
        return request_count > 0

    def get_network_stats(self):
        """Get network statistics"""
        return {
            'node_id': self.node_id,
            'peers_connected': len(self.peers),
            'peers': list(self.peers),
            'chain_length': len(self.blockchain.chain),
            'mempool_size': len(self.blockchain.mempool),
            'running': self.running
        }
    
    def stop(self):
        """Stop the network node"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        print("P2P network node stopped")
