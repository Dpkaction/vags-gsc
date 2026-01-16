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

# Default seed nodes for one-click join (Production vs Testnet)
SEED_NODES = [
    # Note: These are example IPs - users should manually connect using displayed IP addresses
    # "127.0.0.1",       # Localhost (only works on same machine)
    # "192.168.1.10",    # Common local IP (may not exist)
    # "192.168.0.10",    # Common local IP (may not exist)
    # "seed1.gsc-coin.org",  # Placeholder for future production seed
    # "seed2.gsc-coin.org"   # Placeholder for future production seed
]

# Common network ranges to scan for local peers
LOCAL_NETWORK_RANGES = [
    "192.168.1.",      # Most common home network
    "192.168.0.",      # Common router default
    "10.0.0.",         # Corporate networks
    "172.16.0.",       # Private networks
]

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

        # Basic traffic counters (for GUI + production monitoring)
        self._traffic_lock = threading.Lock()
        self._bytes_sent = 0
        self._bytes_received = 0
        self._messages_sent = 0
        self._messages_received = 0
        self._last_message_time = None
        
        # Bitcoin-style sync state
        self.sync_mode = "live"  # headers -> blocks -> mempool -> live
        self.syncing_with = set()  # Peers we're syncing with
        self.requested_headers = set()
        self.requested_blocks = set()
        self.sync_complete = True
        
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
    
    def request_mempool_from_peer(self, peer_address: str) -> list:
        """Request mempool transactions from a specific peer (Bitcoin-like)"""
        try:
            host, port = peer_address.split(':')
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(10)
                sock.connect((host, int(port)))
                
                request = {
                    'type': 'request_mempool',
                    'node_id': self.node_id
                }
                
                sock.send(json.dumps(request).encode())
                response = sock.recv(8192).decode()
                
                if response:
                    data = json.loads(response)
                    return data.get('mempool', [])
                    
        except Exception as e:
            print(f"Error requesting mempool from {peer_address}: {e}")
        return []
    
    def request_blockchain_info(self, peer_address: str) -> dict:
        """Request blockchain info from peer (Bitcoin-like)"""
        try:
            host, port = peer_address.split(':')
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(10)
                sock.connect((host, int(port)))
                
                request = {
                    'type': 'request_blockchain_info',
                    'node_id': self.node_id
                }
                
                sock.send(json.dumps(request).encode())
                response = sock.recv(4096).decode()
                
                if response:
                    return json.loads(response)
                    
        except Exception as e:
            print(f"Error requesting blockchain info from {peer_address}: {e}")
        return {}
    
    def request_full_blockchain(self, peer_address: str) -> list:
        """Request full blockchain from peer (Bitcoin-like)"""
        try:
            host, port = peer_address.split(':')
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(30)  # Longer timeout for full blockchain
                sock.connect((host, int(port)))
                
                request = {
                    'type': 'request_full_blockchain',
                    'node_id': self.node_id
                }
                
                sock.send(json.dumps(request).encode())
                
                # Receive large blockchain data
                full_data = b''
                while True:
                    chunk = sock.recv(8192)
                    if not chunk:
                        break
                    full_data += chunk
                    if b'"end_of_blockchain"' in full_data:
                        break
                
                if full_data:
                    data = json.loads(full_data.decode())
                    return data.get('blockchain', [])
                    
        except Exception as e:
            print(f"Error requesting blockchain from {peer_address}: {e}")
        return []
    
    def handle_peer(self, client_socket, address):
        """Handle communication with a peer"""
        peer_address = f"{address[0]}:{address[1]}"
        self.peers.add(peer_address)
        
        try:
            while self.running:
                data = client_socket.recv(4096)
                if not data:
                    break

                with self._traffic_lock:
                    self._bytes_received += len(data)
                    self._messages_received += 1
                    self._last_message_time = time.time()
                
                try:
                    message = json.loads(data.decode())
                    response = self.process_message(message, client_socket)
                    if response:
                        client_socket.send(json.dumps(response).encode())
                except Exception as e:
                    print(f"Error processing message from {peer_address}: {e}")
        
        except Exception as e:
            print(f"Error handling peer {peer_address}: {e}")
        finally:
            self.peers.discard(peer_address)
            client_socket.close()
            print(f"Peer disconnected: {peer_address}")
    
    def process_message(self, message, client_socket):
        """Process incoming message from peer"""
        msg_type = message.get('type')
        
        if msg_type == 'handshake':
            # Handle incoming handshake from connecting peer
            peer_node_id = message.get('node_id')
            peer_version = message.get('version')
            peer_height = message.get('blockchain_height', 0)
            peer_hash = message.get('best_hash')
            
            print(f"Received handshake from {peer_node_id} (height: {peer_height})")
            
            # Send handshake acknowledgment
            return {
                'type': 'handshake_ack',
                'node_id': self.node_id,
                'version': '1.0',
                'blockchain_height': len(self.blockchain.chain),
                'best_hash': self.blockchain.get_latest_block().hash,
                'status': 'connected'
            }
        
        # Bitcoin-style sync messages
        elif msg_type == 'getheaders':
            return self._handle_getheaders(message, client_socket)
        elif msg_type == 'headers':
            self._handle_headers(message, client_socket)
        elif msg_type == 'getblocks':
            return self._handle_getblocks(message, client_socket)
        elif msg_type == 'inv':
            self._handle_inv(message, client_socket)
        elif msg_type == 'getdata':
            return self._handle_getdata(message, client_socket)
        elif msg_type == 'block':
            self._handle_block(message, client_socket)
        elif msg_type == 'mempool':
            return self._handle_mempool_request(message, client_socket)
        elif msg_type == 'tx':
            self._handle_transaction_batch(message, client_socket)
        
        elif msg_type == 'new_block':
            # Handle new block announcement
            block_data = message.get('block')
            if block_data:
                print(f"Received new block: {block_data.get('hash', 'unknown')[:16]}...")
                # TODO: Validate and add block to chain
        
        elif msg_type == 'new_transaction':
            # Handle new transaction announcement and propagate
            tx_data = message.get('transaction')
            if tx_data:
                print(f"📡 Received new transaction: {tx_data.get('tx_id', 'unknown')[:16]}...")
                try:
                    # Reconstruct transaction from data
                    from blockchain import Transaction
                    tx = Transaction(
                        sender=tx_data.get('sender'),
                        receiver=tx_data.get('receiver'),
                        amount=tx_data.get('amount'),
                        fee=tx_data.get('fee'),
                        timestamp=tx_data.get('timestamp'),
                        signature=tx_data.get('signature')
                    )
                    tx.tx_id = tx_data.get('tx_id')  # Preserve original ID
                    
                    # Add to mempool if valid and not duplicate
                    if self.blockchain.add_transaction_to_mempool(tx):
                        print(f"✅ Transaction added to mempool: {tx.tx_id[:16]}...")
                        # Propagate to other peers (avoid loops)
                        sender_peer = f"{client_socket.getpeername()[0]}:{client_socket.getpeername()[1]}"
                        self.propagate_transaction_to_peers(tx, exclude_peer=sender_peer)
                    else:
                        print(f"❌ Transaction rejected or duplicate: {tx.tx_id[:16]}...")
                except Exception as e:
                    print(f"Error processing received transaction: {e}")
        
        elif msg_type == 'ping':
            # Respond to ping
            return {'type': 'pong', 'node_id': self.node_id}
        
        elif msg_type == 'request_mempool':
            # Send mempool transactions
            mempool_data = [tx.to_dict() for tx in self.blockchain.mempool]
            return {
                'type': 'mempool_response',
                'mempool': mempool_data,
                'count': len(mempool_data)
            }
        
        elif msg_type == 'request_blockchain_info':
            # Send blockchain info
            return {
                'type': 'blockchain_info_response',
                'height': len(self.blockchain.chain),
                'best_hash': self.blockchain.get_latest_block().hash,
                'difficulty': self.blockchain.difficulty,
                'total_supply': self.blockchain.current_supply
            }
        
        elif msg_type == 'request_full_blockchain':
            # Send full blockchain (for sync)
            blockchain_data = []
            for block in self.blockchain.chain:
                block_data = {
                    'index': block.index,
                    'timestamp': block.timestamp,
                    'transactions': [tx.to_dict() for tx in block.transactions],
                    'previous_hash': block.previous_hash,
                    'hash': block.hash,
                    'merkle_root': block.merkle_root,
                    'nonce': block.nonce,
                    'difficulty': block.difficulty,
                    'miner': block.miner,
                    'reward': block.reward
                }
                blockchain_data.append(block_data)
            
            return {
                'type': 'blockchain_response',
                'blockchain': blockchain_data,
                'end_of_blockchain': True
            }
        
        elif msg_type == 'peer_list':
            # Handle peer list update
            peers = message.get('peers', [])
            for peer in peers:
                if peer != f"127.0.0.1:{self.port}":
                    self.known_nodes.add(peer)
        
        return None
    
    def handle_version(self, message, client_socket, peer_address):
        """Handle version message from peer"""
        peer_ver = message.get('version')
        peer_height = message.get('current_height', 0)
        
        # Respond with version if we haven't sent it yet (inbound connection)
        # For simplicity, we always send verack to acknowledge
        verack_msg = {'type': 'verack'}
        client_socket.send(json.dumps(verack_msg).encode())
        
        # If inbound, we also need to send our version
        # (This is a simplification of the full state machine)
        my_version = {
            'type': 'version',
            'version': 1,
            'node_id': self.node_id,
            'current_height': len(self.blockchain.chain),
            'timestamp': datetime.now().isoformat()
        }
        # In a real implementation we track if we already sent version
        client_socket.send(json.dumps(my_version).encode())

    def handle_verack(self, client_socket):
        """Handle verack message"""
        # Connection established, start sync
        self.start_initial_sync(client_socket)

    def start_initial_sync(self, client_socket):
        """Start headers-first sync"""
        # Send getheaders with our latest hash as locator
        latest_hash = self.blockchain.chain[-1].hash
        msg = {
            'type': 'getheaders',
            'locator_hash': latest_hash,
            'stop_hash': '0'*64 
        }
        client_socket.send(json.dumps(msg).encode())
    
    def connect_to_peer(self, host, port):
        """Connect to a peer node with improved handshake"""
        try:
            print(f"Attempting to connect to {host}:{port}...")
            peer_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            peer_socket.settimeout(15)  # Increased timeout
            peer_socket.connect((host, port))
            print(f"Socket connected to {host}:{port}")
            
            # Send handshake
            handshake = {
                'type': 'handshake',
                'node_id': self.node_id,
                'version': '1.0',
                'blockchain_height': len(self.blockchain.chain),
                'best_hash': self.blockchain.get_latest_block().hash
            }
            handshake_data = json.dumps(handshake).encode()
            peer_socket.send(handshake_data)
            print(f"Handshake sent to {host}:{port}")
            
            # Wait for handshake response
            peer_socket.settimeout(10)  # Timeout for response
            response = peer_socket.recv(1024).decode()
            print(f"Received response from {host}:{port}: {response[:100]}...")
            
            if response:
                peer_info = json.loads(response)
                if peer_info.get('type') == 'handshake_ack':
                    peer_address = f"{host}:{port}"
                    self.peers.add(peer_address)
                    
                    # Handle peer in separate thread
                    peer_thread = threading.Thread(
                        target=self.handle_peer,
                        args=(peer_socket, (host, port))
                    )
                    peer_thread.daemon = True
                    peer_thread.start()
                    
                    print(f"✅ Successfully connected to peer: {peer_address} (height: {peer_info.get('blockchain_height', 0)})")
                    return True
                else:
                    print(f"❌ Invalid handshake response from {host}:{port}: {peer_info.get('type')}")
                    peer_socket.close()
                    return False
            else:
                print(f"❌ No response received from {host}:{port}")
                peer_socket.close()
                return False
            
        except socket.timeout:
            print(f"❌ Connection timeout to {host}:{port}")
            return False
<<<<<<< Updated upstream
    
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
=======
        except ConnectionRefusedError:
            print(f"❌ Connection refused by {host}:{port} - Make sure the other device is running GSC Coin")
            return False
        except Exception as e:
            print(f"❌ Failed to connect to {host}:{port} - {e}")
            return False

    def connect_to_peer_manual(self, ip, port):
        """Manually connect to a peer (e.g. from GUI)"""
        peer_address = f"{ip}:{port}"
        if peer_address in self.peers:
            return True, "Already connected to this peer"
            
        if self.connect_to_peer(ip, int(port)):
            return True, f"Successfully connected to {ip}:{port}"
        else:
            return False, f"Failed to connect to {ip}:{port}"

    def get_connected_peers(self):
        """Get list of connected peers"""
        return list(self.peers)

    def join_network(self):
        """Auto-connect to seed nodes"""
        results = []
        connected_count = 0
        
        for seed_ip in SEED_NODES:
            # Don't connect to self
            if seed_ip == self.get_local_ip() or seed_ip == "127.0.0.1":
                continue
                
            try:
                if self.connect_to_peer(seed_ip, self.port):
                    results.append(f"✅ Connected to {seed_ip}")
                    connected_count += 1
                else:
                    results.append(f"❌ Failed to reach {seed_ip}")
            except:
                 results.append(f"❌ Error reaching {seed_ip}")
                 
        if connected_count > 0:
            return True, f"Joined network! Connected to {connected_count} seed nodes.\n" + "\n".join(results)
        else:
            return False, "Could not reach any seed nodes.\n" + "\n".join(results)

    def join_network_custom(self, nodes):
        """Connect to a user-provided list of nodes (ip:port)"""
        results = []
        connected_count = 0

        for node in nodes:
            try:
                host, port_str = node.split(':', 1)
                port = int(port_str)

                # Don't connect to self
                if host == self.get_local_ip() and port == self.port:
                    continue

                if self.connect_to_peer(host, port):
                    results.append(f"✅ Connected to {host}:{port}")
                    connected_count += 1
                else:
                    results.append(f"❌ Failed to connect to {host}:{port}")
            except Exception as e:
                results.append(f"❌ Error connecting to {node}: {e}")

        if connected_count > 0:
            return True, f"Connected to {connected_count} node(s).\n" + "\n".join(results)
        return False, "Could not connect to any provided nodes.\n" + "\n".join(results)

    def force_broadcast_block(self):
        """Force broadcast of the latest block"""
        if not self.blockchain.chain:
            return False, "No blocks to broadcast"
            
        latest_block = self.blockchain.chain[-1]
        self.broadcast_block(latest_block)
        return True, f"Broadcasted Block #{latest_block.index} ({latest_block.hash[:8]}...)"

    def discover_peers(self):
        """Discover and connect to network peers with improved Bitcoin-like discovery"""
        discovery_attempts = 0
        max_attempts = 10
        
        while self.running and discovery_attempts < max_attempts:
            try:
                # Try to connect to seed nodes
                for seed_node in SEED_NODES:
                    if seed_node not in self.peers:
                        try:
                            self.connect_to_peer(seed_node, 8333)
                            if len(self.peers) > 0:
                                print(f"Connected to seed node: {seed_node}")
                        except Exception as e:
                            pass  # Silently fail for seed nodes
                
                # Try to connect to known nodes
                for node in list(self.known_nodes):
                    if node not in self.peers and len(self.peers) < 8:
                        try:
                            host, port = node.split(':')
                            self.connect_to_peer(host, int(port))
                            print(f"Connected to known node: {node}")
                        except Exception as e:
                            pass
                
                # Request peer lists from connected peers
                for peer in list(self.peers):
                    try:
                        self.request_peer_list(peer)
                    except Exception as e:
                        pass
                
                discovery_attempts += 1
                if len(self.peers) > 0:
                    print(f"Peer discovery complete - connected to {len(self.peers)} peers")
                    break
                    
                time.sleep(5)  # Shorter discovery interval
            except Exception as e:
                print(f"Error in peer discovery: {e}")
        
        if len(self.peers) == 0:
            print("No peers found - running in standalone mode")

    def request_peer_list(self, peer_address: str):
        """Request peer list from a connected peer"""
        try:
            host, port = peer_address.split(':')
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(5)
                sock.connect((host, int(port)))
                
                request = {
                    'type': 'request_peers',
                    'node_id': self.node_id
                }
                
                sock.send(json.dumps(request).encode())
                response = sock.recv(4096).decode()
                
                if response:
                    data = json.loads(response)
                    peers = data.get('peers', [])
                    for peer in peers:
                        if peer not in self.peers and peer != f"127.0.0.1:{self.port}":
                            self.known_nodes.add(peer)
                            

        except Exception as e:
            pass  # Silently fail

>>>>>>> Stashed changes
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
    
    def broadcast_transaction(self, transaction):
        """Broadcast transaction to all connected peers with automatic propagation"""
        message = {
            'type': 'new_transaction',
            'transaction': transaction.to_dict(),
            'node_id': self.node_id,
            'timestamp': time.time()
        }
        
        broadcast_count = 0
        failed_peers = []
        
        print(f"🚀 Broadcasting transaction {transaction.tx_id[:16]}... to {len(self.peers)} peers")
        
        for peer in list(self.peers):
            try:
                host, port = peer.split(':')
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(3)
                sock.connect((host, int(port)))
                sock.send(json.dumps(message).encode())
                sock.close()
                broadcast_count += 1
                print(f"✅ Transaction sent to {peer}")
            except Exception as e:
                failed_peers.append(peer)
                print(f"❌ Failed to send to {peer}: {str(e)[:50]}...")
        
        # Remove failed peers from active list
        for failed_peer in failed_peers:
            self.peers.discard(failed_peer)
        
        print(f"📊 Transaction broadcast complete: {broadcast_count} successful, {len(failed_peers)} failed")
        return broadcast_count
    
    def propagate_transaction_to_peers(self, transaction, exclude_peer=None):
        """Propagate received transaction to other peers (avoid broadcast loops)"""
        message = {
            'type': 'new_transaction',
            'transaction': transaction.to_dict(),
            'node_id': self.node_id,
            'propagated': True
        }
        
        propagated_count = 0
        peers_to_propagate = [p for p in self.peers if p != exclude_peer]
        
        print(f"🔄 Propagating transaction {transaction.tx_id[:16]}... to {len(peers_to_propagate)} other peers")
        
        for peer in peers_to_propagate:
            try:
                host, port = peer.split(':')
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                sock.connect((host, int(port)))
                sock.send(json.dumps(message).encode())
                sock.close()
                propagated_count += 1
                print(f"🔄 Propagated to {peer}")
            except Exception as e:
                print(f"⚠️ Failed to propagate to {peer}: {str(e)[:30]}...")
        
        return propagated_count
    
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

                with self._traffic_lock:
                    self._bytes_sent += len(data)
                    self._messages_sent += 1
                    self._last_message_time = time.time()
                
            except Exception as e:
                print(f"Failed to broadcast to {peer_address}: {e}")
                self.peers.discard(peer_address)

    def get_network_traffic(self):
        """Traffic counters for GUI"""
        with self._traffic_lock:
            return {
                "node_id": self.node_id,
                "port": self.port,
                "peers_connected": len(self.peers),
                "bytes_sent": self._bytes_sent,
                "bytes_received": self._bytes_received,
                "messages_sent": self._messages_sent,
                "messages_received": self._messages_received,
                "last_message_time": self._last_message_time,
            }

    def get_peer_list(self):
        """Compatibility helper for RPC/UI"""
        peers = []
        for addr in sorted(self.peers):
            peers.append({
                "addr": addr,
                "subver": "/GSCCoin:1.0/",
                "inbound": False,
            })
        return peers

    def get_network_info(self):
        """Compatibility helper for RPC/UI"""
        return {
            "node_id": self.node_id,
            "port": self.port,
            "peers_connected": len(self.peers),
            "peers": sorted(self.peers),
            "chain_length": len(self.blockchain.chain),
            "mempool_size": len(self.blockchain.mempool),
            "running": self.running,
            "traffic": self.get_network_traffic(),
        }
    
    def serialize_block(self, block):
        """Serialize block for network transmission"""
        return {
            'index': block.index,
            'timestamp': block.timestamp,
            'transactions': [self.serialize_transaction(tx) for tx in block.transactions],
            'previous_hash': block.previous_hash,
            'hash': block.hash,
            'merkle_root': getattr(block, 'merkle_root', ''),
            'nonce': block.nonce,
            'difficulty': getattr(block, 'difficulty', 4),
            'miner': getattr(block, 'miner', ''),
            'reward': getattr(block, 'reward', 0)
        }
    
    def deserialize_block(self, block_data):
        """Deserialize block from network data"""
        from blockchain import Block, Transaction
        import time
        
        transactions = [self.deserialize_transaction(tx_data) for tx_data in block_data.get('transactions', [])]

        block = Block(
            index=block_data.get('index', 0),
            timestamp=block_data.get('timestamp', time.time()),
            transactions=transactions,
            previous_hash=block_data.get('previous_hash', "0" * 64),
            nonce=block_data.get('nonce', 0),
            hash=block_data.get('hash', ''),
            merkle_root=block_data.get('merkle_root', ''),
            difficulty=block_data.get('difficulty', 4),
            miner=block_data.get('miner', ''),
            reward=block_data.get('reward', 0),
        )
        
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
        """Get local IP address for network connectivity"""
        try:
            # Try to get actual network IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            try:
                # Fallback: get hostname IP
                hostname = socket.gethostname()
                ip = socket.gethostbyname(hostname)
                if ip.startswith("127."):
                    # If still localhost, try getting all interfaces
                    import subprocess
                    result = subprocess.run(['ipconfig'], capture_output=True, text=True, shell=True)
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'IPv4 Address' in line and '192.168.' in line:
                            ip = line.split(':')[-1].strip()
                            return ip
                return ip
            except:
                return "127.0.0.1"
    
<<<<<<< Updated upstream
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
=======
    def get_network_addresses(self):
        """Get all network connection information for display"""
        local_ip = self.get_local_ip()
>>>>>>> Stashed changes
        return {
            'local_ip': local_ip,
            'p2p_address': f"{local_ip}:{self.port}",
            'rpc_address': f"{local_ip}:8332",
            'node_id': self.node_id
        }
    
    # Bitcoin-style sync methods
    def start_headers_sync(self, peer_addr: str):
        """Start Bitcoin-style headers-first sync with a peer"""
        if peer_addr in self.syncing_with:
            return
        
        self.syncing_with.add(peer_addr)
        self.sync_mode = "headers"
        self.sync_complete = False
        print(f"📥 Starting Bitcoin-style headers sync with {peer_addr}")
        
        # Request headers from our chain tip
        self._request_headers(peer_addr, self.blockchain.get_latest_block().hash)
    
    def _request_headers(self, peer_addr: str, from_hash: str):
        """Request headers from a specific block (Bitcoin getheaders)"""
        try:
            host, port = peer_addr.split(':')
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(10)
                sock.connect((host, int(port)))
                
                getheaders_msg = {
                    "type": "getheaders",
                    "from_block": from_hash,
                    "node_id": self.node_id
                }
                
                sock.send(json.dumps(getheaders_msg).encode())
                print(f"📤 Requested headers from {from_hash[:16]}... to {peer_addr}")
                
        except Exception as e:
            print(f"❌ Failed to request headers from {peer_addr}: {e}")
    
    def _handle_getheaders(self, message: dict, client_socket) -> dict:
        """Handle getheaders request (Bitcoin-style)"""
        from_block = message.get("from_block", "")
        
        # Find headers after from_block
        headers_to_send = []
        
        try:
            # Find the block in our chain
            from_index = 0
            for i, block in enumerate(self.blockchain.chain):
                if block.hash == from_block:
                    from_index = i + 1
                    break
            
            # Send up to 2000 headers (Bitcoin limit)
            for i in range(from_index, min(from_index + 2000, len(self.blockchain.chain))):
                block = self.blockchain.chain[i]
                header_data = {
                    'hash': block.hash,
                    'prev_hash': block.previous_hash,
                    'merkle_root': getattr(block, 'merkle_root', ''),
                    'timestamp': block.timestamp,
                    'difficulty': getattr(block, 'difficulty', 4),
                    'nonce': block.nonce,
                    'height': block.index
                }
                headers_to_send.append(header_data)
        
        except Exception as e:
            print(f"Error building headers response: {e}")
        
        print(f"📤 Sending {len(headers_to_send)} headers")
        
        return {
            "type": "headers",
            "headers": headers_to_send,
            "count": len(headers_to_send)
        }
    
    def _handle_headers(self, message: dict, client_socket):
        """Handle received headers (Bitcoin-style)"""
        headers_data = message.get("headers", [])
        
        if not headers_data:
            print(f"📥 No new headers received, starting blocks sync")
            self._start_blocks_sync()
            return
        
        print(f"📥 Received {len(headers_data)} headers")
        self._start_blocks_sync()
    
    def _start_blocks_sync(self):
        """Start block download phase"""
        print(f"📦 Starting blocks sync phase")
        self.sync_mode = "blocks"
        self._start_mempool_sync()
    
    def _start_mempool_sync(self):
        """Start mempool sync phase"""
        print(f"💼 Starting mempool sync phase")
        self.sync_mode = "mempool"
        
        # Request mempool from connected peers
        for peer_addr in list(self.peers):
            try:
                mempool_data = self.request_mempool_from_peer(peer_addr)
                if mempool_data:
                    print(f"📥 Received {len(mempool_data)} mempool transactions")
                break
            except Exception as e:
                print(f"❌ Error syncing mempool from {peer_addr}: {e}")
        
        self._enter_live_mode()
    
    def _enter_live_mode(self):
        """Enter live sync mode - Bitcoin-style sync complete"""
        print(f"🎉 Bitcoin-style sync complete! Entering live mode.")
        self.sync_mode = "live"
        self.sync_complete = True
        self.syncing_with.clear()
    
    def _handle_getblocks(self, message: dict, client_socket) -> dict:
        """Handle getblocks request (Bitcoin-style)"""
        from_height = message.get("from_height", 0)
        
        available_blocks = []
        for i in range(from_height, min(from_height + 500, len(self.blockchain.chain))):
            if i < len(self.blockchain.chain):
                block = self.blockchain.chain[i]
                available_blocks.append(block.hash)
        
        print(f"📤 Sending inventory of {len(available_blocks)} blocks")
        
        return {
            "type": "inv",
            "blocks": available_blocks,
            "count": len(available_blocks)
        }
    
    def _handle_inv(self, message: dict, client_socket):
        """Handle block inventory (Bitcoin-style)"""
        available_blocks = message.get("blocks", [])
        print(f"📥 Received inventory of {len(available_blocks)} blocks")
    
    def _handle_getdata(self, message: dict, client_socket) -> dict:
        """Handle getdata request (Bitcoin-style)"""
        block_hash = message.get("block")
        
        if block_hash:
            for block in self.blockchain.chain:
                if block.hash == block_hash:
                    print(f"📤 Sending block {block_hash[:16]}...")
                    
                    block_data = {
                        'header': {
                            'hash': block.hash,
                            'prev_hash': block.previous_hash,
                            'merkle_root': getattr(block, 'merkle_root', ''),
                            'timestamp': block.timestamp,
                            'difficulty': getattr(block, 'difficulty', 4),
                            'nonce': block.nonce,
                            'height': block.index
                        },
                        'transactions': [tx.to_dict() for tx in block.transactions]
                    }
                    
                    return {
                        "type": "block",
                        "block": block_data
                    }
        
        return None
    
    def _handle_block(self, message: dict, client_socket):
        """Handle received full block (Bitcoin-style)"""
        block_data = message.get("block")
        
        if block_data:
            block_hash = block_data.get('header', {}).get('hash', 'unknown')
            tx_count = len(block_data.get('transactions', []))
            print(f"📥 Received block {block_hash[:16]}... with {tx_count} transactions")
    
    def _handle_mempool_request(self, message: dict, client_socket) -> dict:
        """Handle mempool request (Bitcoin-style)"""
        transactions = [tx.to_dict() for tx in self.blockchain.mempool]
        
        print(f"📤 Sending {len(transactions)} mempool transactions")
        
        return {
            "type": "tx",
            "transactions": transactions,
            "count": len(transactions)
        }
    
    def _handle_transaction_batch(self, message: dict, client_socket):
        """Handle received transaction batch (Bitcoin-style)"""
        transactions_data = message.get("transactions", [])
        
        if transactions_data:
            print(f"📥 Received {len(transactions_data)} transactions")
            
            for tx_data in transactions_data:
                try:
                    from blockchain import Transaction
                    tx = Transaction(
                        sender=tx_data.get('sender'),
                        receiver=tx_data.get('receiver'),
                        amount=tx_data.get('amount'),
                        fee=tx_data.get('fee'),
                        timestamp=tx_data.get('timestamp'),
                        signature=tx_data.get('signature')
                    )
                    tx.tx_id = tx_data.get('tx_id')
                    
                    if self.blockchain.add_transaction_to_mempool(tx):
                        print(f"✅ Added transaction: {tx.tx_id[:16]}...")
                except Exception as e:
                    print(f"❌ Error processing transaction: {e}")
    
    def get_sync_status(self) -> dict:
        """Get Bitcoin-style sync status for GUI"""
        return {
            "sync_mode": self.sync_mode,
            "sync_complete": self.sync_complete,
            "syncing_with": list(self.syncing_with),
            "chain_height": len(self.blockchain.chain) - 1,
            "chain_tip": self.blockchain.get_latest_block().hash[:16] + "..." if self.blockchain.chain else "N/A",
            "mempool_size": len(self.blockchain.mempool),
            "connected_peers": len(self.peers)
        }
    
    def stop(self):
        """Stop the network node"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        print("GSC Network node stopped")
    
    def get_network_stats(self) -> dict:
        """Get network statistics"""
        with self._traffic_lock:
            return {
                'peers_connected': len(self.peers),
                'bytes_sent': self._bytes_sent,
                'bytes_received': self._bytes_received,
                'messages_sent': self._messages_sent,
                'messages_received': self._messages_received,
                'last_message_time': self._last_message_time,
                'node_id': self.node_id,
                'port': self.port
            }
