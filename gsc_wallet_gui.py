import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext, simpledialog
import threading
import time
import json
import sys
import os
from datetime import datetime
import hashlib
import base64
from blockchain import GSCBlockchain, Transaction, Block
from wallet_manager import WalletManager
from paper_wallet_generator import PaperWalletGenerator

class GSCWalletGUI:
    def __init__(self, blockchain=None, network_node=None):
        self.root = tk.Tk()
        self.root.title("GSC Coin - Professional Cryptocurrency Wallet")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # Set window icon and styling similar to Bitcoin Core
        self.root.resizable(True, True)
        
        # Configure ttk style for Bitcoin Core look
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Configure colors similar to Bitcoin Core
        self.style.configure('TNotebook', background='#f0f0f0')
        self.style.configure('TNotebook.Tab', padding=[20, 8])
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TLabelFrame', background='#f0f0f0')
        self.style.configure('TLabel', background='#f0f0f0', foreground='#333333')
        self.style.configure('Title.TLabel', font=('Arial', 12, 'bold'))
        self.style.configure('Balance.TLabel', font=('Arial', 18, 'bold'), foreground='#2e7d32')
        
        # Initialize blockchain and network
        self.blockchain = blockchain if blockchain else GSCBlockchain()
        self.network_node = network_node
        self.wallet_manager = WalletManager()
        self.paper_wallet_generator = PaperWalletGenerator(self.root)
        self.current_address = "GSC1qw508d6qejxtdg4y5r3zarvary0c5xw7kv8f3t4"  # Genesis address
        self.current_balance = 0.0
        self.mining_thread = None
        self.is_mining = False
        self.network_peers = []
        self.sync_status = "Synchronizing with network..."
        self.total_supply = 21750000000000  # 21.75 trillion GSC
        
        # Create menu system first
        self.create_menu_system()
        
        # Create GUI
        self.create_gui()
        
        # Create status bar
        self.create_status_bar()
        
        # Load existing blockchain if available
        self.blockchain.load_blockchain("gsc_blockchain.json")
        self.update_displays()
    
    def create_menu_system(self):
        """Create Bitcoin Core-style menu system"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Create Wallet...", command=self.create_new_wallet)
        file_menu.add_command(label="Open Wallet", command=self.open_wallet_dialog)
        file_menu.add_command(label="Close Wallet...", command=self.close_current_wallet)
        file_menu.add_command(label="Close All Wallets...", command=self.close_all_wallets)
        file_menu.add_separator()
        file_menu.add_command(label="Backup Wallet...", command=self.backup_wallet_dialog)
        file_menu.add_command(label="Restore Wallet...", command=self.restore_wallet_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Generate Paper Wallet...", command=self.generate_paper_wallet)
        file_menu.add_separator()
        file_menu.add_command(label="Sign message...", command=self.sign_message_dialog)
        file_menu.add_command(label="Verify message...", command=self.verify_message_dialog)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", accelerator="Ctrl+Q", command=self.root.quit)
        
        # Settings Menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Encrypt Wallet...", command=self.encrypt_wallet_dialog)
        settings_menu.add_command(label="Change Passphrase...", command=self.change_passphrase_dialog)
        settings_menu.add_separator()
        settings_menu.add_checkbutton(label="Mask values", command=self.toggle_mask_values)
        settings_menu.add_separator()
        settings_menu.add_command(label="Options...", command=self.show_options_dialog)
        
        # Window Menu
        window_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Window", menu=window_menu)
        window_menu.add_command(label="Minimize", accelerator="Ctrl+M", command=self.root.iconify)
        window_menu.add_separator()
        window_menu.add_command(label="Sending addresses", command=self.show_sending_addresses)
        window_menu.add_command(label="Receiving addresses", command=self.show_receiving_addresses)
        window_menu.add_separator()
        window_menu.add_command(label="Information", accelerator="Ctrl+I", command=self.show_information)
        window_menu.add_command(label="Console", accelerator="Ctrl+T", command=self.show_console)
        window_menu.add_command(label="Network Traffic", command=self.show_network_traffic)
        window_menu.add_command(label="Peers", command=self.show_peers)
        
        # Tools Menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Download Wallet .exe", command=self.download_wallet_exe)
        tools_menu.add_command(label="Create Portable Version", command=self.create_portable_version)
        
        # Help Menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About GSC Coin", command=self.show_about)
        help_menu.add_command(label="Command-line options", command=self.show_command_options)
        
        # Bind keyboard shortcuts
        self.root.bind('<Control-q>', lambda e: self.root.quit())
        self.root.bind('<Control-m>', lambda e: self.root.iconify())
        self.root.bind('<Control-i>', lambda e: self.show_information())
        self.root.bind('<Control-t>', lambda e: self.show_console())
    
    def create_status_bar(self):
        """Create status bar like Bitcoin Core"""
        self.status_frame = ttk.Frame(self.root)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Status labels
        self.sync_label = ttk.Label(self.status_frame, text="Synchronizing with network...")
        self.sync_label.pack(side=tk.LEFT, padx=5)
        
        self.blocks_label = ttk.Label(self.status_frame, text="0 blocks")
        self.blocks_label.pack(side=tk.LEFT, padx=5)
        
        self.peers_label = ttk.Label(self.status_frame, text="0 peers")
        self.peers_label.pack(side=tk.RIGHT, padx=5)
    
    def create_gui(self):
        # Create main frame
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.create_wallet_tab()
        self.create_send_tab()
        self.create_receive_tab()
        self.create_mining_tab()
        self.create_mempool_tab()
        self.create_blockchain_tab()
        self.create_network_tab()
        self.create_console_tab()
    
    def create_wallet_tab(self):
        # Wallet Tab
        wallet_frame = ttk.Frame(self.notebook)
        self.notebook.add(wallet_frame, text="Overview")
        
        # Balance section - Bitcoin Core style
        balance_frame = ttk.LabelFrame(wallet_frame, text="Available Balance", padding=15)
        balance_frame.pack(fill=tk.X, padx=15, pady=10)
        
        # Main balance display
        balance_container = ttk.Frame(balance_frame)
        balance_container.pack(fill=tk.X)
        
        ttk.Label(balance_container, text="GSC Balance:", style='Title.TLabel').pack(side=tk.LEFT)
        self.balance_label = ttk.Label(balance_container, text="0.00000000 GSC", style='Balance.TLabel')
        self.balance_label.pack(side=tk.RIGHT)
        
        # Market info display
        market_frame = ttk.LabelFrame(wallet_frame, text="Market Information", padding=10)
        market_frame.pack(fill=tk.X, padx=15, pady=5)
        
        # Total supply info
        supply_info = ttk.Frame(market_frame)
        supply_info.pack(fill=tk.X)
        
        ttk.Label(supply_info, text="Total Supply:").pack(side=tk.LEFT)
        ttk.Label(supply_info, text=f"{self.total_supply:,.0f} GSC", 
                 font=("Arial", 10, "bold"), foreground="#2e7d32").pack(side=tk.RIGHT)
        
        # Current address display
        addr_frame = ttk.Frame(market_frame)
        addr_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(addr_frame, text="Current Address:").pack(side=tk.LEFT)
        self.address_display = ttk.Label(addr_frame, text=self.current_address[:20] + "...", 
                                        font=("Courier", 9), foreground="#1976d2")
        self.address_display.pack(side=tk.RIGHT)
        
        # Transaction section
        tx_frame = ttk.LabelFrame(wallet_frame, text="Send GSC Coins", padding=10)
        tx_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(tx_frame, text="Recipient Address:").grid(row=0, column=0, sticky=tk.W)
        self.recipient_entry = ttk.Entry(tx_frame, width=40)
        self.recipient_entry.grid(row=0, column=1, padx=5)
        
        ttk.Label(tx_frame, text="Amount:").grid(row=1, column=0, sticky=tk.W)
        self.amount_entry = ttk.Entry(tx_frame, width=20)
        self.amount_entry.grid(row=1, column=1, padx=5, sticky=tk.W)
        
        ttk.Label(tx_frame, text="Fee:").grid(row=2, column=0, sticky=tk.W)
        self.fee_entry = ttk.Entry(tx_frame, width=20)
        self.fee_entry.grid(row=2, column=1, padx=5, sticky=tk.W)
        self.fee_entry.insert(0, "1.0")
        
        ttk.Button(tx_frame, text="Send Transaction", command=self.send_transaction).grid(row=3, column=0, columnspan=2, pady=10)
        
        # Transaction history
        history_frame = ttk.LabelFrame(wallet_frame, text="Transaction History", padding=10)
        history_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.tx_history = ttk.Treeview(history_frame, columns=("Type", "Amount", "Address", "Time"), show="headings")
        self.tx_history.heading("Type", text="Type")
        self.tx_history.heading("Amount", text="Amount")
        self.tx_history.heading("Address", text="Address")
        self.tx_history.heading("Time", text="Time")
        self.tx_history.pack(fill=tk.BOTH, expand=True)
    
    def create_send_tab(self):
        """Create Send tab like Bitcoin Core"""
        send_frame = ttk.Frame(self.notebook)
        self.notebook.add(send_frame, text="Send")
        
        # Send form
        send_form = ttk.LabelFrame(send_frame, text="Send GSC Coins", padding=15)
        send_form.pack(fill=tk.X, padx=15, pady=10)
        
        # Pay To
        ttk.Label(send_form, text="Pay To:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.send_address_entry = ttk.Entry(send_form, width=50)
        self.send_address_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(send_form, text="Address Book", command=self.open_address_book).grid(row=0, column=2, padx=5)
        
        # Label
        ttk.Label(send_form, text="Label:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.send_label_entry = ttk.Entry(send_form, width=50)
        self.send_label_entry.grid(row=1, column=1, padx=5, pady=5)
        
        # Amount
        ttk.Label(send_form, text="Amount:").grid(row=2, column=0, sticky=tk.W, pady=5)
        amount_frame = ttk.Frame(send_form)
        amount_frame.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)
        self.send_amount_entry = ttk.Entry(amount_frame, width=20)
        self.send_amount_entry.pack(side=tk.LEFT)
        ttk.Label(amount_frame, text="GSC").pack(side=tk.LEFT, padx=(5, 0))
        
        # Fee
        ttk.Label(send_form, text="Fee:").grid(row=3, column=0, sticky=tk.W, pady=5)
        fee_frame = ttk.Frame(send_form)
        fee_frame.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)
        self.send_fee_entry = ttk.Entry(fee_frame, width=20)
        self.send_fee_entry.pack(side=tk.LEFT)
        self.send_fee_entry.insert(0, "0.001")
        ttk.Label(fee_frame, text="GSC").pack(side=tk.LEFT, padx=(5, 0))
        
        # Buttons
        button_frame = ttk.Frame(send_form)
        button_frame.grid(row=4, column=1, sticky=tk.W, pady=10)
        ttk.Button(button_frame, text="Clear All", command=self.clear_send_form).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Send", command=self.send_transaction_advanced).pack(side=tk.LEFT)
    
    def create_receive_tab(self):
        """Create Receive tab like Bitcoin Core"""
        receive_frame = ttk.Frame(self.notebook)
        self.notebook.add(receive_frame, text="Receive")
        
        # Request payment section
        request_frame = ttk.LabelFrame(receive_frame, text="Request Payment", padding=15)
        request_frame.pack(fill=tk.X, padx=15, pady=10)
        
        # Label
        ttk.Label(request_frame, text="Label:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.receive_label_entry = ttk.Entry(request_frame, width=40)
        self.receive_label_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Amount
        ttk.Label(request_frame, text="Amount:").grid(row=1, column=0, sticky=tk.W, pady=5)
        amount_frame = ttk.Frame(request_frame)
        amount_frame.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        self.receive_amount_entry = ttk.Entry(amount_frame, width=20)
        self.receive_amount_entry.pack(side=tk.LEFT)
        ttk.Label(amount_frame, text="GSC").pack(side=tk.LEFT, padx=(5, 0))
        
        # Message
        ttk.Label(request_frame, text="Message:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.receive_message_entry = ttk.Entry(request_frame, width=40)
        self.receive_message_entry.grid(row=2, column=1, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(request_frame)
        button_frame.grid(row=3, column=1, sticky=tk.W, pady=10)
        ttk.Button(button_frame, text="Clear", command=self.clear_receive_form).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Request payment", command=self.create_payment_request).pack(side=tk.LEFT)
        ttk.Button(button_frame, text="Show QR Code", command=self.show_qr_code).pack(side=tk.LEFT, padx=(5, 0))
        
        # Current address display
        address_frame = ttk.LabelFrame(receive_frame, text="Your Address", padding=15)
        address_frame.pack(fill=tk.X, padx=15, pady=10)
        
        self.current_address_label = ttk.Label(address_frame, text=self.current_address, font=("Courier", 10))
        self.current_address_label.pack()
        
        ttk.Button(address_frame, text="Copy Address", command=self.copy_address).pack(pady=5)
        ttk.Button(address_frame, text="Generate New Address", command=self.generate_new_address_gui).pack()
    
    def create_mining_tab(self):
        # Mining Tab
        mining_frame = ttk.Frame(self.notebook)
        self.notebook.add(mining_frame, text="⛏️ Mining")
        
        # Mining controls
        controls_frame = ttk.LabelFrame(mining_frame, text="Mining Controls", padding=10)
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.mining_button = ttk.Button(controls_frame, text="Start Mining", command=self.toggle_mining)
        self.mining_button.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(controls_frame, text="Difficulty:").pack(side=tk.LEFT, padx=5)
        self.difficulty_var = tk.StringVar(value=str(self.blockchain.difficulty))
        difficulty_spin = ttk.Spinbox(controls_frame, from_=1, to=8, textvariable=self.difficulty_var, width=5)
        difficulty_spin.pack(side=tk.LEFT, padx=5)
        
        # Mining stats
        stats_frame = ttk.LabelFrame(mining_frame, text="Mining Statistics", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.mining_status = ttk.Label(stats_frame, text="Status: Idle")
        self.mining_status.pack(anchor=tk.W)
        
        self.nonce_label = ttk.Label(stats_frame, text="Nonce: 0")
        self.nonce_label.pack(anchor=tk.W)
        
        self.hash_rate_label = ttk.Label(stats_frame, text="Hash Rate: 0 H/s")
        self.hash_rate_label.pack(anchor=tk.W)
        
        self.current_hash_label = ttk.Label(stats_frame, text="Current Hash: -")
        self.current_hash_label.pack(anchor=tk.W)
        
        # Block details
        block_frame = ttk.LabelFrame(mining_frame, text="Current Block Details", padding=10)
        block_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.block_details = scrolledtext.ScrolledText(block_frame, height=15, wrap=tk.WORD)
        self.block_details.pack(fill=tk.BOTH, expand=True)
    
    def create_mempool_tab(self):
        # Mempool Tab
        mempool_frame = ttk.Frame(self.notebook)
        self.notebook.add(mempool_frame, text="📋 Mempool")
        
        # Mempool stats
        stats_frame = ttk.LabelFrame(mempool_frame, text="Mempool Statistics", padding=10)
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.mempool_size_label = ttk.Label(stats_frame, text="Pending Transactions: 0")
        self.mempool_size_label.pack(anchor=tk.W)
        
        self.mempool_fees_label = ttk.Label(stats_frame, text="Total Fees: 0.0 GSC")
        self.mempool_fees_label.pack(anchor=tk.W)
        
        # Mempool transactions
        tx_frame = ttk.LabelFrame(mempool_frame, text="Pending Transactions", padding=10)
        tx_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.mempool_tree = ttk.Treeview(tx_frame, columns=("TxID", "From", "To", "Amount", "Fee"), show="headings")
        self.mempool_tree.heading("TxID", text="Transaction ID")
        self.mempool_tree.heading("From", text="From")
        self.mempool_tree.heading("To", text="To")
        self.mempool_tree.heading("Amount", text="Amount")
        self.mempool_tree.heading("Fee", text="Fee")
        
        # Add scrollbar
        mempool_scroll = ttk.Scrollbar(tx_frame, orient=tk.VERTICAL, command=self.mempool_tree.yview)
        self.mempool_tree.configure(yscrollcommand=mempool_scroll.set)
        
        self.mempool_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        mempool_scroll.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_blockchain_tab(self):
        # Blockchain Tab
        blockchain_frame = ttk.Frame(self.notebook)
        self.notebook.add(blockchain_frame, text="🔗 Blockchain")
        
        # Blockchain info
        info_frame = ttk.LabelFrame(blockchain_frame, text="Blockchain Information", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.blocks_label = ttk.Label(info_frame, text="Total Blocks: 0")
        self.blocks_label.pack(anchor=tk.W)
        
        self.chain_valid_label = ttk.Label(info_frame, text="Chain Valid: True")
        self.chain_valid_label.pack(anchor=tk.W)
        
        # Blocks list
        blocks_frame = ttk.LabelFrame(blockchain_frame, text="Blocks", padding=10)
        blocks_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.blocks_tree = ttk.Treeview(blocks_frame, columns=("Index", "Hash", "PrevHash", "Nonce", "Txs", "Miner"), show="headings")
        self.blocks_tree.heading("Index", text="Block #")
        self.blocks_tree.heading("Hash", text="Hash")
        self.blocks_tree.heading("PrevHash", text="Previous Hash")
        self.blocks_tree.heading("Nonce", text="Nonce")
        self.blocks_tree.heading("Txs", text="Transactions")
        self.blocks_tree.heading("Miner", text="Miner")
        
        # Add scrollbar
        blocks_scroll = ttk.Scrollbar(blocks_frame, orient=tk.VERTICAL, command=self.blocks_tree.yview)
        self.blocks_tree.configure(yscrollcommand=blocks_scroll.set)
        
        self.blocks_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        blocks_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click to show block details
        self.blocks_tree.bind("<Double-1>", self.show_block_details)
    
    def create_network_tab(self):
        # Network Tab
        network_frame = ttk.Frame(self.notebook)
        self.notebook.add(network_frame, text="🌐 Network")
        
        # Network controls
        controls_frame = ttk.LabelFrame(network_frame, text="Network Controls", padding=10)
        controls_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(controls_frame, text="Save Blockchain", command=self.save_blockchain).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Load Blockchain", command=self.load_blockchain).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Validate Chain", command=self.validate_chain).pack(side=tk.LEFT, padx=5)
        
        # Network info
        info_frame = ttk.LabelFrame(network_frame, text="Network Information", padding=10)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.network_info = scrolledtext.ScrolledText(info_frame, height=20, wrap=tk.WORD)
        self.network_info.pack(fill=tk.BOTH, expand=True)
    
    def create_console_tab(self):
        """Create Console tab for debug commands"""
        console_frame = ttk.Frame(self.notebook)
        self.notebook.add(console_frame, text="Console")
        
        # Console output
        console_output_frame = ttk.LabelFrame(console_frame, text="Console Output", padding=10)
        console_output_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.console_output = scrolledtext.ScrolledText(console_output_frame, height=20, wrap=tk.WORD, bg='black', fg='green', font=('Courier', 10))
        self.console_output.pack(fill=tk.BOTH, expand=True)
        
        # Add download button
        download_frame = ttk.Frame(console_frame)
        download_frame.pack(fill=tk.X, pady=5)
        
        download_exe_btn = ttk.Button(download_frame, text="📥 Download Wallet .exe", 
                                     command=self.simple_download_exe)
        download_exe_btn.pack(side=tk.LEFT, padx=5)
        
        # Console input
        input_frame = ttk.Frame(console_frame)
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(input_frame, text=">").pack(side=tk.LEFT)
        self.console_input = ttk.Entry(input_frame)
        self.console_input.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.console_input.bind('<Return>', self.execute_console_command)
        
        ttk.Button(input_frame, text="Execute", command=self.execute_console_command).pack(side=tk.RIGHT)
        
        # Add welcome message
        self.console_output.insert(tk.END, "GSC Coin Console\n")
        self.console_output.insert(tk.END, "Type 'help' for available commands\n")
        self.console_output.insert(tk.END, "=" * 50 + "\n")
    
    def send_transaction(self):
        try:
            recipient = self.recipient_entry.get().strip()
            amount = float(self.amount_entry.get())
            fee = float(self.fee_entry.get())
            
            if not recipient:
                messagebox.showerror("Error", "Please enter recipient address")
                return
            
            if amount <= 0:
                messagebox.showerror("Error", "Amount must be positive")
                return
            
            # Check balance
            balance = self.blockchain.get_balance(self.current_address)
            if balance < (amount + fee):
                messagebox.showerror("Error", f"Insufficient balance. Available: {balance} GSC")
                return
            
            # Create transaction
            tx = Transaction(
                sender=self.current_address,
                receiver=recipient,
                amount=amount,
                fee=fee,
                timestamp=time.time()
            )
            
            # Add to mempool
            if self.blockchain.add_transaction_to_mempool(tx):
                messagebox.showinfo("Success", f"Transaction added to mempool!\nTX ID: {tx.tx_id[:16]}...")
                self.recipient_entry.delete(0, tk.END)
                self.amount_entry.delete(0, tk.END)
                self.update_displays()
            else:
                messagebox.showerror("Error", "Failed to add transaction to mempool")
        
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for amount and fee")
        except Exception as e:
            messagebox.showerror("Error", f"Transaction failed: {str(e)}")
    
    def toggle_mining(self):
        if not self.is_mining:
            self.start_mining()
        else:
            self.stop_mining()
    
    def start_mining(self):
        if len(self.blockchain.mempool) == 0:
            messagebox.showwarning("Warning", "No transactions in mempool to mine")
            return
        
        self.is_mining = True
        self.mining_button.config(text="Stop Mining")
        self.blockchain.difficulty = int(self.difficulty_var.get())
        
        # Start mining in separate thread
        self.mining_thread = threading.Thread(target=self.mine_block)
        self.mining_thread.daemon = True
        self.mining_thread.start()
    
    def stop_mining(self):
        self.is_mining = False
        self.mining_button.config(text="Start Mining")
        self.mining_status.config(text="Status: Stopped")
    
    def mine_block(self):
        def mining_callback(stats):
            if self.is_mining:
                self.root.after(0, lambda: self.update_mining_stats(stats))
        
        try:
            self.root.after(0, lambda: self.mining_status.config(text="Status: Mining..."))
            
            mined_block = self.blockchain.mine_pending_transactions(self.current_address, mining_callback)
            
            if mined_block and self.is_mining:
                self.root.after(0, lambda: self.on_block_mined(mined_block))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Mining Error", str(e)))
        finally:
            self.is_mining = False
            self.root.after(0, lambda: self.mining_button.config(text="Start Mining"))
    
    def update_mining_stats(self, stats):
        self.nonce_label.config(text=f"Nonce: {stats['nonce']:,}")
        self.hash_rate_label.config(text=f"Hash Rate: {stats['hash_rate']:.0f} H/s")
        
        # Update block details
        if hasattr(self.blockchain, 'current_mining_block'):
            block = self.blockchain.current_mining_block
            details = f"Block Index: {block.index}\n"
            details += f"Previous Hash: {block.previous_hash}\n"
            details += f"Merkle Root: {block.merkle_root}\n"
            details += f"Difficulty: {block.difficulty}\n"
            details += f"Current Nonce: {stats['nonce']}\n"
            details += f"Current Hash: {block.hash}\n"
            details += f"Target: {'0' * block.difficulty}{'*' * (64 - block.difficulty)}\n\n"
            details += f"Transactions ({len(block.transactions)}):\n"
            for i, tx in enumerate(block.transactions):
                details += f"{i+1}. {tx.sender} -> {tx.receiver}: {tx.amount} GSC (Fee: {tx.fee})\n"
            
            self.block_details.delete(1.0, tk.END)
            self.block_details.insert(1.0, details)
    
    def on_block_mined(self, block):
        self.mining_status.config(text=f"Status: Block {block.index} Mined!")
        messagebox.showinfo("Mining Success", f"Block {block.index} successfully mined!\nHash: {block.hash[:16]}...\nReward: {block.reward} GSC")
        self.update_displays()
        self.is_mining = False
    
    def update_displays(self):
        # Update balance - Bitcoin Core format (get actual balance from blockchain)
        if hasattr(self, 'current_address') and self.current_address:
            balance = self.blockchain.get_balance(self.current_address)
        else:
            balance = 0.0
        self.balance_label.config(text=f"{balance:.8f} GSC")
        
        # Update mempool
        self.update_mempool_display()
        
        # Update blockchain display
        self.update_blockchain_display()
        
        # Update transaction history
        self.update_transaction_history()
        
        # Update network info
        self.update_network_info()
    
    def update_mempool_display(self):
        # Clear mempool tree
        for item in self.mempool_tree.get_children():
            self.mempool_tree.delete(item)
        
        # Update status bar with nodes and height
        blocks_count = len(self.blockchain.chain)
        blockchain_height = blocks_count - 1 if blocks_count > 0 else 0
        nodes_count = len(self.blockchain.nodes)
        mempool_count = len(self.blockchain.mempool)
        
        self.blocks_label.config(text=f"Height: {blockchain_height} | Blocks: {blocks_count} | Mempool: {mempool_count}")
        self.peers_label.config(text=f"Connected Nodes: {nodes_count}")
        
        # Update sync status with more details
        if blockchain_height > 0:
            current_reward = self.blockchain.get_current_reward()
            self.sync_label.config(text=f"Synced - Height {blockchain_height} | Reward: {current_reward} GSC")
        
        # Update mempool stats
        total_fees = sum(tx.fee for tx in self.blockchain.mempool)
        
        self.mempool_size_label.config(text=f"Pending Transactions: {mempool_count}")
        self.mempool_fees_label.config(text=f"Total Fees: {total_fees:.2f} GSC")
        
        # Add transactions to tree
        for tx in self.blockchain.mempool:
            self.mempool_tree.insert("", tk.END, values=(
                tx.tx_id[:16] + "...",
                tx.sender,
                tx.receiver,
                f"{tx.amount:.2f}",
                f"{tx.fee:.2f}"
            ))
    
    def start_mining_fixed(self):
        if len(self.blockchain.mempool) == 0:
            messagebox.showwarning("Warning", "No transactions in mempool to mine")
            return
            
        self.is_mining = True
        self.mining_button.config(text="Stop Mining")
        self.blockchain.difficulty = int(self.difficulty_var.get())
            
        # Start mining in separate thread
        self.mining_thread = threading.Thread(target=self.mine_block)
        self.mining_thread.daemon = True
        self.mining_thread.start()
    
    def update_blockchain_display(self):
        # Clear blockchain tree
        for item in self.blocks_tree.get_children():
            self.blocks_tree.delete(item)
        
        # Add blocks to tree
        for block in self.blockchain.chain:
            self.blocks_tree.insert("", tk.END, values=(
                block.index,
                datetime.fromtimestamp(block.timestamp).strftime("%Y-%m-%d %H:%M:%S"),
                block.hash[:16] + "...",
                block.previous_hash[:16] + "...",
                block.nonce,
                len(block.transactions),
                block.miner
            ))
    
    def update_transaction_history(self):
        # Clear transaction history
        for item in self.tx_history.get_children():
            self.tx_history.delete(item)
        
        # Add relevant transactions
        for block in self.blockchain.chain:
            for tx in block.transactions:
                if tx.sender == self.current_address or tx.receiver == self.current_address:
                    tx_type = "Sent" if tx.sender == self.current_address else "Received"
                    address = tx.receiver if tx.sender == self.current_address else tx.sender
                    amount = f"-{tx.amount + tx.fee}" if tx.sender == self.current_address else f"+{tx.amount}"
                    
                    self.tx_history.insert("", 0, values=(
                        tx_type,
                        amount,
                        address,
                        datetime.fromtimestamp(tx.timestamp).strftime("%Y-%m-%d %H:%M:%S")
                    ))
    
    def update_network_info(self):
        info = self.blockchain.get_blockchain_info()
        network_text = f"=== GSC Coin Network Information ===\n\n"
        network_text += f"Blockchain Height: {info['blocks']} blocks\n"
        network_text += f"Current Difficulty: {info['difficulty']}\n"
        network_text += f"Mempool Size: {info['mempool_size']} transactions\n"
        network_text += f"Total Addresses: {info['total_addresses']}\n"
        network_text += f"Mining Status: {'Active' if info['is_mining'] else 'Idle'}\n"
        network_text += f"Latest Block Hash: {info['latest_block_hash']}\n"
        network_text += f"Chain Validity: {info['chain_valid']}\n\n"
        
        network_text += "=== Account Balances ===\n"
        for address, balance in self.blockchain.balances.items():
            network_text += f"{address}: {balance:.2f} GSC\n"
        
        self.network_info.delete(1.0, tk.END)
        self.network_info.insert(1.0, network_text)
    
    def show_block_details(self, event):
        selection = self.blocks_tree.selection()
        if selection:
            item = self.blocks_tree.item(selection[0])
            block_index = int(item['values'][0])
            block = self.blockchain.chain[block_index]
            
            # Create new window for block details
            detail_window = tk.Toplevel(self.root)
            detail_window.title(f"GSC Block {block_index} Details")
            detail_window.geometry("600x500")
            
            details_text = scrolledtext.ScrolledText(detail_window, wrap=tk.WORD)
            details_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            block_info = f"=== GSC Block {block.index} Details ===\n\n"
            block_info += f"Index: {block.index}\n"
            block_info += f"Timestamp: {datetime.fromtimestamp(block.timestamp)}\n"
            block_info += f"Hash: {block.hash}\n"
            block_info += f"Previous Hash: {block.previous_hash}\n"
            block_info += f"Merkle Root: {block.merkle_root}\n"
            block_info += f"Nonce: {block.nonce:,}\n"
            block_info += f"Difficulty: {block.difficulty}\n"
            block_info += f"Miner: {block.miner}\n"
            block_info += f"Reward: {block.reward} GSC\n\n"
            block_info += f"Transactions ({len(block.transactions)}):\n"
            
            for i, tx in enumerate(block.transactions):
                block_info += f"\n{i+1}. Transaction ID: {tx.tx_id}\n"
                block_info += f"   From: {tx.sender}\n"
                block_info += f"   To: {tx.receiver}\n"
                block_info += f"   Amount: {tx.amount} GSC\n"
                block_info += f"   Fee: {tx.fee} GSC\n"
                block_info += f"   Time: {datetime.fromtimestamp(tx.timestamp)}\n"
            
            details_text.insert(1.0, block_info)
    
    def save_blockchain(self):
        try:
            self.blockchain.save_blockchain("gsc_blockchain.json")
            messagebox.showinfo("Success", "Blockchain saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save blockchain: {str(e)}")
    
    def load_blockchain(self):
        try:
            self.blockchain.load_blockchain("gsc_blockchain.json")
            self.update_displays()
            messagebox.showinfo("Success", "Blockchain loaded successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load blockchain: {str(e)}")
    
    def validate_chain(self):
        is_valid = self.blockchain.is_chain_valid()
        if is_valid:
            # Update displays to show correct balances after validation
            self.update_displays()
            messagebox.showinfo("Validation", "Blockchain is valid!\nBalances have been updated.")
        else:
            messagebox.showerror("Validation", "Blockchain is invalid!")
    
    def run(self):
        # Start update loop
        self.update_loop()
        self.root.mainloop()
    
    def update_loop(self):
        # Update displays every 2 seconds
        self.update_displays()
        self.root.after(2000, self.update_loop)
    
    # ===== MENU COMMAND IMPLEMENTATIONS =====
    
    def create_new_wallet(self):
        """Create new wallet dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Create New Wallet")
        dialog.geometry("400x300")
        dialog.resizable(False, False)
        
        ttk.Label(dialog, text="Wallet Name:").pack(pady=10)
        name_entry = ttk.Entry(dialog, width=30)
        name_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Passphrase (optional):").pack(pady=(20, 5))
        pass_entry = ttk.Entry(dialog, width=30, show="*")
        pass_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Confirm Passphrase:").pack(pady=(10, 5))
        confirm_entry = ttk.Entry(dialog, width=30, show="*")
        confirm_entry.pack(pady=5)
        
        def create_wallet():
            name = name_entry.get().strip()
            passphrase = pass_entry.get()
            confirm = confirm_entry.get()
            
            if not name:
                messagebox.showerror("Error", "Please enter wallet name")
                return
            
            if passphrase and passphrase != confirm:
                messagebox.showerror("Error", "Passphrases do not match")
                return
            
            try:
                result = self.wallet_manager.create_wallet(name, passphrase if passphrase else None)
                self.current_address = result['address']
                self.current_balance = result['balance']
                
                # Create detailed wallet info dialog
                info_dialog = tk.Toplevel(self.root)
                info_dialog.title("Wallet Created Successfully")
                info_dialog.geometry("600x500")
                
                # Header
                ttk.Label(info_dialog, text=f"Wallet '{name}' Created Successfully!", 
                         font=('Arial', 14, 'bold')).pack(pady=10)
                
                # Wallet details frame
                details_frame = ttk.LabelFrame(info_dialog, text="Wallet Details", padding=10)
                details_frame.pack(fill=tk.X, padx=20, pady=10)
                
                # Address info
                ttk.Label(details_frame, text="Address:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
                addr_entry = ttk.Entry(details_frame, width=60)
                addr_entry.insert(0, result['address'])
                addr_entry.config(state='readonly')
                addr_entry.pack(fill=tk.X, pady=2)
                
                # Private key info
                ttk.Label(details_frame, text="Private Key:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(10,0))
                priv_entry = ttk.Entry(details_frame, width=60, show="*")
                priv_entry.insert(0, result['private_key'])
                priv_entry.config(state='readonly')
                priv_entry.pack(fill=tk.X, pady=2)
                
                # Public key info
                ttk.Label(details_frame, text="Public Key:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(10,0))
                pub_entry = ttk.Entry(details_frame, width=60)
                pub_entry.insert(0, result['public_key'])
                pub_entry.config(state='readonly')
                pub_entry.pack(fill=tk.X, pady=2)
                
                # Balance info
                ttk.Label(details_frame, text=f"Starting Balance: {result['balance']:.8f} GSC", 
                         font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=(10,0))
                
                # Backup seed frame
                seed_frame = ttk.LabelFrame(info_dialog, text="IMPORTANT: Backup Seed Phrase", padding=10)
                seed_frame.pack(fill=tk.X, padx=20, pady=10)
                
                seed_text = tk.Text(seed_frame, height=3, wrap=tk.WORD)
                seed_text.insert(1.0, result['backup_seed'])
                seed_text.config(state=tk.DISABLED)
                seed_text.pack(fill=tk.X)
                
                ttk.Label(seed_frame, text="Keep this seed phrase safe - it's needed to recover your wallet!", 
                         foreground="red", font=('Arial', 9, 'bold')).pack(pady=5)
                
                # Buttons
                button_frame = ttk.Frame(info_dialog)
                button_frame.pack(fill=tk.X, padx=20, pady=10)
                
                def show_qr():
                    self.show_address_qr(result['address'])
                
                def copy_address():
                    self.root.clipboard_clear()
                    self.root.clipboard_append(result['address'])
                    messagebox.showinfo("Copied", "Address copied to clipboard")
                
                ttk.Button(button_frame, text="Show QR Code", command=show_qr).pack(side=tk.LEFT, padx=5)
                ttk.Button(button_frame, text="Copy Address", command=copy_address).pack(side=tk.LEFT, padx=5)
                ttk.Button(button_frame, text="Close", command=info_dialog.destroy).pack(side=tk.RIGHT, padx=5)
                
                dialog.destroy()
                self.update_displays()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create wallet: {str(e)}")
        
        ttk.Button(dialog, text="Create Wallet", command=create_wallet).pack(pady=20)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack()
    
    def open_wallet_dialog(self):
        """Open wallet dialog"""
        wallets = self.wallet_manager.list_wallets()
        if not wallets:
            messagebox.showinfo("Info", "No wallets found. Create a new wallet first.")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Open Wallet")
        dialog.geometry("400x250")
        
        ttk.Label(dialog, text="Select Wallet:").pack(pady=10)
        wallet_var = tk.StringVar()
        wallet_combo = ttk.Combobox(dialog, textvariable=wallet_var, values=wallets, state="readonly")
        wallet_combo.pack(pady=5)
        
        ttk.Label(dialog, text="Passphrase (if encrypted):").pack(pady=(20, 5))
        pass_entry = ttk.Entry(dialog, width=30, show="*")
        pass_entry.pack(pady=5)
        
        def open_wallet():
            wallet_name = wallet_var.get()
            passphrase = pass_entry.get()
            
            if not wallet_name:
                messagebox.showerror("Error", "Please select a wallet")
                return
            
            try:
                result = self.wallet_manager.open_wallet(wallet_name, passphrase if passphrase else None)
                self.current_address = result['address']
                
                # Get ACTUAL balance from blockchain (not from wallet file)
                self.current_balance = self.blockchain.get_balance(self.current_address)
                
                success_msg = f"Wallet '{wallet_name}' opened successfully!\n\n"
                success_msg += f"Address: {result['address']}\n"
                success_msg += f"Balance: {self.current_balance:.8f} GSC\n"
                success_msg += f"Addresses: {result['addresses_count']}"
                
                messagebox.showinfo("Wallet Opened", success_msg)
                dialog.destroy()
                self.update_displays()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open wallet: {str(e)}")
        
        ttk.Button(dialog, text="Open Wallet", command=open_wallet).pack(pady=20)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack()
    
    def close_current_wallet(self):
        """Close current wallet"""
        if self.wallet_manager.current_wallet:
            self.wallet_manager.close_wallet()
            messagebox.showinfo("Info", "Wallet closed")
            self.update_displays()
        else:
            messagebox.showinfo("Info", "No wallet is currently open")
    
    def close_all_wallets(self):
        """Close all wallets"""
        self.close_current_wallet()
    
    def backup_wallet_dialog(self):
        """Backup wallet dialog"""
        if not self.wallet_manager.current_wallet:
            messagebox.showerror("Error", "No wallet is currently open")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Backup Wallet",
            defaultextension=".backup",
            filetypes=[("Backup files", "*.backup"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                self.wallet_manager.backup_wallet(filename)
                messagebox.showinfo("Success", f"Wallet backed up to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Backup failed: {str(e)}")
    
    def restore_wallet_dialog(self):
        """Restore wallet dialog"""
        filename = filedialog.askopenfilename(
            title="Restore Wallet",
            filetypes=[("Backup files", "*.backup"), ("All files", "*.*")]
        )
        
        if filename:
            new_name = simpledialog.askstring("Restore Wallet", "Enter new wallet name:")
            if new_name:
                try:
                    result = self.wallet_manager.restore_wallet(filename, new_name)
                    messagebox.showinfo("Success", f"Wallet restored as '{new_name}'")
                except Exception as e:
                    messagebox.showerror("Error", f"Restore failed: {str(e)}")
    
    def encrypt_wallet_dialog(self):
        """Encrypt wallet dialog"""
        if not self.wallet_manager.current_wallet:
            messagebox.showerror("Error", "No wallet is currently open")
            return
        
        if self.wallet_manager.is_encrypted:
            messagebox.showinfo("Info", "Wallet is already encrypted")
            return
        
        passphrase = simpledialog.askstring("Encrypt Wallet", "Enter passphrase:", show='*')
        if passphrase:
            confirm = simpledialog.askstring("Encrypt Wallet", "Confirm passphrase:", show='*')
            if passphrase == confirm:
                try:
                    self.wallet_manager.encrypt_wallet(passphrase)
                    messagebox.showinfo("Success", "Wallet encrypted successfully")
                except Exception as e:
                    messagebox.showerror("Error", f"Encryption failed: {str(e)}")
            else:
                messagebox.showerror("Error", "Passphrases do not match")
    
    def change_passphrase_dialog(self):
        """Change passphrase dialog"""
        if not self.wallet_manager.current_wallet:
            messagebox.showerror("Error", "No wallet is currently open")
            return
        
        if not self.wallet_manager.is_encrypted:
            messagebox.showinfo("Info", "Wallet is not encrypted")
            return
        
        old_pass = simpledialog.askstring("Change Passphrase", "Enter current passphrase:", show='*')
        if old_pass:
            new_pass = simpledialog.askstring("Change Passphrase", "Enter new passphrase:", show='*')
            if new_pass:
                confirm = simpledialog.askstring("Change Passphrase", "Confirm new passphrase:", show='*')
                if new_pass == confirm:
                    try:
                        self.wallet_manager.change_passphrase(old_pass, new_pass)
                        messagebox.showinfo("Success", "Passphrase changed successfully")
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to change passphrase: {str(e)}")
                else:
                    messagebox.showerror("Error", "New passphrases do not match")
    
    def sign_message_dialog(self):
        """Sign message dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Sign Message")
        dialog.geometry("500x400")
        
        ttk.Label(dialog, text="Address:").pack(pady=5)
        addr_entry = ttk.Entry(dialog, width=60)
        addr_entry.pack(pady=5)
        addr_entry.insert(0, self.current_address)
        
        ttk.Label(dialog, text="Message:").pack(pady=(20, 5))
        msg_text = scrolledtext.ScrolledText(dialog, height=8, width=60)
        msg_text.pack(pady=5)
        
        ttk.Label(dialog, text="Signature:").pack(pady=(20, 5))
        sig_text = scrolledtext.ScrolledText(dialog, height=4, width=60)
        sig_text.pack(pady=5)
        
        def sign_message():
            address = addr_entry.get()
            message = msg_text.get(1.0, tk.END).strip()
            
            if not message:
                messagebox.showerror("Error", "Please enter a message")
                return
            
            # Simple signature (in real implementation, use proper cryptographic signing)
            signature = hashlib.sha256(f"{address}{message}".encode()).hexdigest()
            sig_text.delete(1.0, tk.END)
            sig_text.insert(1.0, signature)
        
        ttk.Button(dialog, text="Sign Message", command=sign_message).pack(pady=10)
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack()
    
    def verify_message_dialog(self):
        """Verify message dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Verify Message")
        dialog.geometry("500x450")
        
        ttk.Label(dialog, text="Address:").pack(pady=5)
        addr_entry = ttk.Entry(dialog, width=60)
        addr_entry.pack(pady=5)
        
        ttk.Label(dialog, text="Message:").pack(pady=(20, 5))
        msg_text = scrolledtext.ScrolledText(dialog, height=8, width=60)
        msg_text.pack(pady=5)
        
        ttk.Label(dialog, text="Signature:").pack(pady=(20, 5))
        sig_entry = ttk.Entry(dialog, width=60)
        sig_entry.pack(pady=5)
        
        result_label = ttk.Label(dialog, text="", foreground="blue")
        result_label.pack(pady=10)
        
        def verify_message():
            address = addr_entry.get()
            message = msg_text.get(1.0, tk.END).strip()
            signature = sig_entry.get()
            
            if not all([address, message, signature]):
                messagebox.showerror("Error", "Please fill all fields")
                return
            
            # Simple verification (in real implementation, use proper cryptographic verification)
            expected_sig = hashlib.sha256(f"{address}{message}".encode()).hexdigest()
            if signature == expected_sig:
                result_label.config(text="✓ Message signature verified", foreground="green")
            else:
                result_label.config(text="✗ Message signature invalid", foreground="red")
        
        ttk.Button(dialog, text="Verify Message", command=verify_message).pack(pady=10)
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack()
    
    def toggle_mask_values(self):
        """Toggle value masking"""
        # Implementation for masking sensitive values
        pass
    
    def show_options_dialog(self):
        """Show options dialog"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Options")
        dialog.geometry("600x500")
        
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Main tab
        main_frame = ttk.Frame(notebook)
        notebook.add(main_frame, text="Main")
        
        ttk.Label(main_frame, text="Mining Difficulty:").pack(pady=10)
        diff_var = tk.StringVar(value=str(self.blockchain.difficulty))
        ttk.Spinbox(main_frame, from_=1, to=8, textvariable=diff_var).pack()
        
        # Network tab
        network_frame = ttk.Frame(notebook)
        notebook.add(network_frame, text="Network")
        
        ttk.Label(network_frame, text="Network settings will be implemented here").pack(pady=20)
        
        def save_options():
            self.blockchain.difficulty = int(diff_var.get())
            messagebox.showinfo("Success", "Options saved")
            dialog.destroy()
        
        ttk.Button(dialog, text="OK", command=save_options).pack(side=tk.RIGHT, padx=10, pady=10)
        ttk.Button(dialog, text="Cancel", command=dialog.destroy).pack(side=tk.RIGHT, pady=10)
    
    def show_sending_addresses(self):
        """Show sending addresses window"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Sending Addresses")
        dialog.geometry("600x400")
        
        # Address list
        tree = ttk.Treeview(dialog, columns=("Label", "Address"), show="headings")
        tree.heading("Label", text="Label")
        tree.heading("Address", text="Address")
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Load sending addresses
        for addr_info in self.wallet_manager.get_sending_addresses():
            tree.insert("", tk.END, values=(addr_info['label'], addr_info['address']))
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        def add_address():
            addr = simpledialog.askstring("Add Address", "Enter address:")
            if addr:
                label = simpledialog.askstring("Add Address", "Enter label:")
                if label:
                    self.wallet_manager.add_sending_address(addr, label)
                    tree.insert("", tk.END, values=(label, addr))
        
        ttk.Button(button_frame, text="Add", command=add_address).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def show_receiving_addresses(self):
        """Show receiving addresses window"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Receiving Addresses")
        dialog.geometry("600x400")
        
        # Address list
        tree = ttk.Treeview(dialog, columns=("Label", "Address", "Created"), show="headings")
        tree.heading("Label", text="Label")
        tree.heading("Address", text="Address")
        tree.heading("Created", text="Created")
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Load receiving addresses
        for addr_info in self.wallet_manager.get_receiving_addresses():
            tree.insert("", tk.END, values=(addr_info['label'], addr_info['address'], addr_info['created']))
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=5)
        
        def new_address():
            label = simpledialog.askstring("New Address", "Enter label:")
            if label:
                addr = self.wallet_manager.generate_new_address(label)
                tree.insert("", tk.END, values=(label, addr, datetime.now().isoformat()))
        
        ttk.Button(button_frame, text="New", command=new_address).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side=tk.RIGHT, padx=5)
    
    def show_information(self):
        """Show blockchain information window"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Information")
        dialog.geometry("500x400")
        
        info_text = scrolledtext.ScrolledText(dialog, wrap=tk.WORD)
        info_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        info = self.blockchain.get_blockchain_info()
        wallet_info = self.wallet_manager.get_wallet_info()
        
        info_content = f"""GSC Coin Information
{'=' * 30}

Blockchain:
- Blocks: {info['blocks']}
- Difficulty: {info['difficulty']}
- Mempool Size: {info['mempool_size']}
- Chain Valid: {info['chain_valid']}

Wallet:
- Name: {wallet_info.get('name', 'None')}
- Encrypted: {wallet_info.get('encrypted', False)}
- Addresses: {wallet_info.get('addresses_count', 0)}
- Master Address: {wallet_info.get('master_address', 'None')}

Network:
- Peers: {len(self.network_peers)}
- Sync Status: {self.sync_status}
"""
        
        info_text.insert(1.0, info_content)
        info_text.config(state=tk.DISABLED)
        
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
    
    def show_console(self):
        """Show console window"""
        # Switch to console tab
        for i in range(self.notebook.index("end")):
            if self.notebook.tab(i, "text") == "Console":
                self.notebook.select(i)
                break
    
    def show_network_traffic(self):
        """Show network traffic window"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Network Traffic")
        dialog.geometry("600x400")
        
        ttk.Label(dialog, text="Network traffic monitoring will be implemented here").pack(pady=20)
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
    
    def show_peers(self):
        """Show peers window"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Peers")
        dialog.geometry("600x400")
        
        # Peers list
        tree = ttk.Treeview(dialog, columns=("Address", "Version", "Height"), show="headings")
        tree.heading("Address", text="Address")
        tree.heading("Version", text="Version")
        tree.heading("Height", text="Height")
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add sample peers (in real implementation, show actual network peers)
        tree.insert("", tk.END, values=("127.0.0.1:8333", "GSC/1.0", "1024"))
        
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
    
    def download_wallet_exe(self):
        """Download wallet as .exe file for other devices"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Download GSC Coin Wallet")
        dialog.geometry("500x400")
        dialog.configure(bg='#f0f0f0')
        
        # Header
        header_frame = ttk.Frame(dialog)
        header_frame.pack(fill=tk.X, padx=20, pady=20)
        
        ttk.Label(header_frame, text="Download GSC Coin Wallet", 
                 font=('Arial', 16, 'bold')).pack()
        ttk.Label(header_frame, text="Create a standalone .exe file for other devices").pack(pady=5)
        
        # Info section
        info_frame = ttk.LabelFrame(dialog, text="Distribution Package", padding=15)
        info_frame.pack(fill=tk.X, padx=20, pady=10)
        
        info_text = """The downloadable package includes:
• GSC_Coin_Wallet.exe (Standalone executable)
• Complete blockchain and wallet functionality
• 21.75 trillion GSC total supply
• Bitcoin-like reward halving system
• Real GSC addresses and market values
• No installation required - runs on any Windows device"""
        
        ttk.Label(info_frame, text=info_text, justify=tk.LEFT).pack()
        
        # Progress section
        progress_frame = ttk.Frame(dialog)
        progress_frame.pack(fill=tk.X, padx=20, pady=10)
        
        build_progress = ttk.Progressbar(progress_frame, mode='indeterminate')
        build_progress.pack(fill=tk.X, pady=5)
        
        build_status = ttk.Label(progress_frame, text="Ready to build executable")
        build_status.pack()
        
        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(fill=tk.X, padx=20, pady=20)
        
        def start_build():
            """Start building the executable"""
            build_progress.start()
            build_status.config(text="Building executable... Please wait...")
            
            def build_thread():
                try:
                    import subprocess
                    import os
                    
                    # Create build script
                    build_script = '''
import subprocess
import sys
import os

def build_exe():
    try:
        # Install PyInstaller if not available
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        
        # Build the executable
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--onefile",
            "--windowed",
            "--name=GSC_Coin_Wallet",
            "--add-data=blockchain.py;.",
            "--add-data=wallet_manager.py;.",
            "--add-data=paper_wallet_generator.py;.",
            "gsc_wallet_gui.py"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode == 0, result.stderr
        
    except Exception as e:
        return False, str(e)

if __name__ == "__main__":
    success, error = build_exe()
    if success:
        print("SUCCESS")
    else:
        print(f"ERROR: {error}")
'''
                    
                    # Write and run build script
                    with open('build_temp.py', 'w') as f:
                        f.write(build_script)
                    # Run the fixed executable builder
                    result = subprocess.run([
                        sys.executable, "build_exe_fixed.py"
                    ], capture_output=True, text=True, cwd=os.getcwd())
                    
                    # Clean up
                    if os.path.exists('build_temp.py'):
                        os.remove('build_temp.py')
                    
                    def update_ui():
                        build_progress.stop()
                        if "SUCCESS" in result.stdout:
                            build_status.config(text=" Executable built successfully!")
                            
                            success_msg = """GSC Coin Wallet executable created successfully!

Location: dist/GSC_Coin_Wallet.exe
Features included:
• 21.75 trillion GSC total supply
• Bitcoin-like reward halving system
• Real market addresses and values
• Complete blockchain functionality
• Professional interface

The executable is ready for distribution to other devices!"""
                            
                            messagebox.showinfo("Build Complete", success_msg)
                            
                            # Ask if user wants to open the dist folder
                            if messagebox.askyesno("Open Folder", "Open the dist folder to see the files?"):
                                try:
                                    os.startfile("dist")
                                except:
                                    pass
                        else:
                            build_status.config(text=" Build failed - Installing PyInstaller...")
                            # Try to install PyInstaller and show instructions
                            install_msg = """Build requires PyInstaller. Please run:

pip install pyinstaller

Then try building again. Or use the portable version instead."""
                            messagebox.showwarning("PyInstaller Required", install_msg)
                    
                    dialog.after(0, update_ui)
                    
                except Exception as error:
                    def show_error():
                        build_progress.stop()
                        build_status.config(text=" Build error occurred")
                        messagebox.showerror("Error", f"Build error: {str(error)}")
                    
                    dialog.after(0, show_error)
            
            # Start build in background thread
            threading.Thread(target=build_thread, daemon=True).start()
        
        ttk.Button(button_frame, text="Build .exe File", command=start_build).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Close", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def create_portable_version(self):
        """Create portable version of the wallet"""
        try:
            import shutil
            import os
            
            # Create portable folder
            portable_dir = "GSC_Wallet_Portable"
            if os.path.exists(portable_dir):
                shutil.rmtree(portable_dir)
            os.makedirs(portable_dir)
            
            # Copy essential files
            files_to_copy = [
                'gsc_wallet_gui.py',
                'blockchain.py',
                'wallet_manager.py',
                'paper_wallet_generator.py',
                'launch_gsc_coin.py',
                'requirements.txt'
            ]
            
            for file in files_to_copy:
                if os.path.exists(file):
                    shutil.copy2(file, portable_dir)
            
            # Create launcher batch file
            launcher_content = '''@echo off
echo Starting GSC Coin Wallet...
python launch_gsc_coin.py
pause'''
            
            with open(os.path.join(portable_dir, 'Start_GSC_Wallet.bat'), 'w') as f:
                f.write(launcher_content)
            
            # Create README
            readme_content = '''GSC Coin Wallet - Portable Version
==================================

Total Supply: 21.75 Trillion GSC
Bitcoin-like reward halving system
Real market addresses and values

Requirements:
- Python 3.7 or higher
- Required packages (install with: pip install -r requirements.txt)

To run:
1. Double-click Start_GSC_Wallet.bat
   OR
2. Run: python launch_gsc_coin.py

Features:
- Complete GSC blockchain functionality
- Professional wallet management
- Mining with proof of work
- Transaction processing
'''
            
            with open(os.path.join(portable_dir, 'README.txt'), 'w') as f:
                f.write(readme_content)
            
            messagebox.showinfo("Success", f"Portable version created in '{portable_dir}' folder!")
            
            # Ask if user wants to open the folder
            if messagebox.askyesno("Open Folder", "Open the portable folder?"):
                try:
                    os.startfile(portable_dir)
                except:
                    pass
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create portable version: {str(e)}")
    
    def show_about(self):
        """Show about dialog"""
        about_text = f"""GSC Coin - Professional Cryptocurrency Wallet

Version: 2.0 (Market Ready)
Total Supply: {self.blockchain.max_supply:,.0f} GSC (21.75 Trillion)
Current Reward: {self.blockchain.get_current_reward()} GSC
Blockchain Height: {len(self.blockchain.chain) - 1}
Connected Nodes: {len(self.blockchain.nodes)}

Features:
• Complete blockchain from genesis block
• Bitcoin-like reward halving system
• Professional Bitcoin Core-style interface
• Real-time mining with nonce visualization
• Transaction mempool management
• Wallet encryption and backup
• Paper wallet generation with QR codes
• Downloadable .exe distribution
• Network synchronization

Built with Python and Tkinter for cross-platform compatibility."""
        
        messagebox.showinfo("About GSC Coin", about_text)
    
    def show_command_options(self):
        """Show command line options"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Command-line Options")
        dialog.geometry("500x300")
        
        options_text = scrolledtext.ScrolledText(dialog, wrap=tk.WORD)
        options_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        options_content = """GSC Coin Command-line Options:

python gsc_professional_wallet.py [options]

Options:
  --datadir=<dir>     Specify data directory
  --testnet          Use test network
  --rpcport=<port>   Set RPC port
  --help             Show this help message

Examples:
  python gsc_professional_wallet.py --datadir=./data
  python gsc_professional_wallet.py --testnet
"""
        
        options_text.insert(1.0, options_content)
        options_text.config(state=tk.DISABLED)
        
        ttk.Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)
    
    def execute_console_command(self, event=None):
        """Execute console command"""
        command = self.console_input.get().strip()
        if not command:
            return
        
        self.console_output.insert(tk.END, f"> {command}\n")
        self.console_input.delete(0, tk.END)
        
        # Process commands
        if command == "help":
            help_text = """Available commands:
help - Show this help
getblockcount - Get number of blocks
getbalance - Get wallet balance
getnewaddress - Generate new address
sendtoaddress <address> <amount> - Send GSC coins
getblockchaininfo - Get blockchain information
listwallets - List available wallets
"""
            self.console_output.insert(tk.END, help_text)
        
        elif command == "getblockcount":
            self.console_output.insert(tk.END, f"{len(self.blockchain.chain)}\n")
        
        elif command == "getbalance":
            balance = self.blockchain.get_balance(self.current_address)
            self.console_output.insert(tk.END, f"{balance:.8f}\n")
        
        elif command == "getnewaddress":
            if self.wallet_manager.current_wallet:
                addr = self.wallet_manager.generate_new_address("Console Generated")
                self.console_output.insert(tk.END, f"{addr}\n")
            else:
                self.console_output.insert(tk.END, "No wallet open\n")
        
        elif command == "getblockchaininfo":
            info = self.blockchain.get_blockchain_info()
            self.console_output.insert(tk.END, f"{json.dumps(info, indent=2)}\n")
        
        elif command == "listwallets":
            wallets = self.wallet_manager.list_wallets()
            self.console_output.insert(tk.END, f"{json.dumps(wallets, indent=2)}\n")
        
        else:
            self.console_output.insert(tk.END, f"Unknown command: {command}\n")
        
        self.console_output.see(tk.END)
    
    # Additional helper methods for new tabs
    def clear_send_form(self):
        """Clear send form"""
        self.send_address_entry.delete(0, tk.END)
        self.send_label_entry.delete(0, tk.END)
        self.send_amount_entry.delete(0, tk.END)
    
    def send_transaction_advanced(self):
        """Advanced send transaction"""
        try:
            recipient = self.send_address_entry.get().strip()
            amount = float(self.send_amount_entry.get())
            fee = float(self.send_fee_entry.get())
            
            if not recipient or amount <= 0:
                messagebox.showerror("Error", "Please enter valid recipient and amount")
                return
            
            # Create and send transaction
            tx = Transaction(
                sender=self.current_address,
                receiver=recipient,
                amount=amount,
                fee=fee,
                timestamp=time.time()
            )
            
            if self.blockchain.add_transaction_to_mempool(tx):
                messagebox.showinfo("Success", f"Transaction sent!\nTX ID: {tx.tx_id[:16]}...")
                self.clear_send_form()
                self.update_displays()
            else:
                messagebox.showerror("Error", "Failed to send transaction")
        
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers")
        except Exception as e:
            messagebox.showerror("Error", f"Transaction failed: {str(e)}")
    
    def clear_receive_form(self):
        """Clear receive form"""
        self.receive_label_entry.delete(0, tk.END)
        self.receive_amount_entry.delete(0, tk.END)
        self.receive_message_entry.delete(0, tk.END)
    
    def create_payment_request(self):
        """Create payment request"""
        label = self.receive_label_entry.get()
        amount = self.receive_amount_entry.get()
        message = self.receive_message_entry.get()
        
        request_info = f"GSC Payment Request\n"
        request_info += f"Address: {self.current_address}\n"
        if label:
            request_info += f"Label: {label}\n"
        if amount:
            request_info += f"Amount: {amount} GSC\n"
        if message:
            request_info += f"Message: {message}\n"
        
        messagebox.showinfo("Payment Request", request_info)
    
    def show_address_qr(self, address):
        """Show QR code for specific address"""
        try:
            import qrcode
            from PIL import Image, ImageTk
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(address)
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Show QR code in new window
            qr_window = tk.Toplevel(self.root)
            qr_window.title("Address QR Code")
            qr_window.geometry("350x400")
            
            # Convert PIL image to PhotoImage
            qr_photo = ImageTk.PhotoImage(qr_img)
            qr_label = ttk.Label(qr_window, image=qr_photo)
            qr_label.image = qr_photo  # Keep a reference
            qr_label.pack(pady=10)
            
            ttk.Label(qr_window, text=address, font=("Courier", 8), wraplength=300).pack(pady=5)
            
            # Buttons
            button_frame = ttk.Frame(qr_window)
            button_frame.pack(pady=10)
            
            def copy_addr():
                self.root.clipboard_clear()
                self.root.clipboard_append(address)
                messagebox.showinfo("Copied", "Address copied to clipboard")
            
            ttk.Button(button_frame, text="Copy Address", command=copy_addr).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Close", command=qr_window.destroy).pack(side=tk.LEFT, padx=5)
            
        except ImportError:
            messagebox.showinfo("Info", f"QR Code libraries not available.\nAddress: {address}")
    
    def simple_download_exe(self):
        """Direct download like Bitcoin Core - no dependencies needed"""
        try:
            import os
            import shutil
            
            # Check if pre-built .exe exists
            exe_path = "dist/GSC_Coin_Wallet.exe"
            
            if os.path.exists(exe_path):
                size_mb = os.path.getsize(exe_path) / (1024 * 1024)
                
                success_msg = f"""✅ GSC Coin Wallet Ready for Download!

📁 Location: {os.path.abspath(exe_path)}
📊 Size: {size_mb:.1f} MB

🚀 Just like Bitcoin Core:
• No installation required
• No dependencies needed
• Complete standalone executable
• Works on any Windows device
• Ready to distribute immediately

🎯 Features included:
• Complete GSC blockchain (21.75 trillion supply)
• Bitcoin-like mining and rewards
• Professional wallet interface
• Locked difficulty at 4
• All dependencies bundled

The .exe file is ready for immediate download!"""
                
                messagebox.showinfo("Download Ready", success_msg)
                
                # Ask to open folder
                if messagebox.askyesno("Open Download Folder", "Open the dist folder to access your downloadable .exe file?"):
                    try:
                        os.startfile("dist")
                    except:
                        pass
            else:
                # If .exe doesn't exist, show message that it needs to be built first
                build_msg = """GSC Coin Wallet .exe not found.

Would you like to build it now? This will create a standalone .exe file that users can download directly without any dependencies (just like Bitcoin Core).

The build process will take a few minutes but only needs to be done once."""
                
                if messagebox.askyesno("Build Required", build_msg):
                    self.build_exe_for_download()
                    
        except Exception as e:
            messagebox.showerror("Error", f"Download preparation failed: {str(e)}")
    
    def build_exe_for_download(self):
        """Build .exe for download distribution"""
        try:
            import subprocess
            import threading
            
            def build_process():
                try:
                    # Show progress dialog
                    progress_dialog = tk.Toplevel(self.root)
                    progress_dialog.title("Building Downloadable .exe")
                    progress_dialog.geometry("450x200")
                    progress_dialog.resizable(False, False)
                    
                    ttk.Label(progress_dialog, text="Creating Bitcoin Core-style Download", 
                             font=('Arial', 12, 'bold')).pack(pady=20)
                    
                    progress_bar = ttk.Progressbar(progress_dialog, mode='indeterminate')
                    progress_bar.pack(pady=10, padx=20, fill=tk.X)
                    progress_bar.start()
                    
                    status_label = ttk.Label(progress_dialog, text="Building standalone executable...")
                    status_label.pack(pady=10)
                    
                    # Run the build script
                    result = subprocess.run([
                        sys.executable, 'build_exe_fixed.py'
                    ], capture_output=True, text=True, cwd=os.getcwd())
                    
                    progress_bar.stop()
                    progress_dialog.destroy()
                    
                    if result.returncode == 0:
                        # Success - now show download ready message
                        self.simple_download_exe()
                    else:
                        messagebox.showerror("Build Failed", f"Failed to create downloadable .exe.\n\nError: {result.stderr}")
                        
                except Exception as e:
                    if 'progress_dialog' in locals():
                        progress_dialog.destroy()
                    messagebox.showerror("Error", f"Build process failed: {str(e)}")
            
            # Run build in background thread
            threading.Thread(target=build_process, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start build process: {str(e)}")
    
    def create_setup_installer(self):
        """Direct download Bitcoin Core-style setup.exe installer"""
        try:
            import os
            
            # Check if pre-built setup.exe exists
            setup_path = "dist/gsc-coin-2.0-win64-setup.exe"
            
            if os.path.exists(setup_path):
                size_mb = os.path.getsize(setup_path) / (1024 * 1024)
                
                success_msg = f"""✅ Bitcoin Core-style Setup.exe Ready!

📁 File: {os.path.abspath(setup_path)}
📊 Size: {size_mb:.1f} MB

🎯 Perfect Bitcoin Core-style installer:
• Professional Windows installer
• Setup wizard with license agreement
• Installs to Program Files
• Creates desktop & start menu shortcuts
• Includes uninstaller
• No dependencies required

🚀 Ready for distribution like bitcoincore.org!

Users can download and run this setup.exe on any Windows device - just like Bitcoin Core!"""
                
                messagebox.showinfo("Setup Ready for Download", success_msg)
                
                # Ask to open folder
                if messagebox.askyesno("Open Download Folder", "Open the dist folder to access your setup.exe?"):
                    try:
                        os.startfile("dist")
                    except:
                        pass
            else:
                # If setup.exe doesn't exist, offer to create it
                build_msg = """Bitcoin Core-style setup.exe not found.

Would you like to create it now? This will build a professional Windows installer that works exactly like Bitcoin Core's setup.exe.

Users will be able to download and install GSC Coin just like they install Bitcoin Core."""
                
                if messagebox.askyesno("Create Setup", build_msg):
                    self.build_setup_for_download()
                    
        except Exception as e:
            messagebox.showerror("Error", f"Setup preparation failed: {str(e)}")
    
    def build_setup_for_download(self):
        """Build setup.exe for download distribution"""
        try:
            import subprocess
            import threading
            
            def build_process():
                try:
                    # Show progress dialog
                    progress_dialog = tk.Toplevel(self.root)
                    progress_dialog.title("Creating Bitcoin Core Setup")
                    progress_dialog.geometry("450x200")
                    progress_dialog.resizable(False, False)
                    
                    ttk.Label(progress_dialog, text="Building Bitcoin Core-style Setup.exe", 
                             font=('Arial', 12, 'bold')).pack(pady=20)
                    
                    progress_bar = ttk.Progressbar(progress_dialog, mode='indeterminate')
                    progress_bar.pack(pady=10, padx=20, fill=tk.X)
                    progress_bar.start()
                    
                    status_label = ttk.Label(progress_dialog, text="Creating professional installer...")
                    status_label.pack(pady=10)
                    
                    # Run the setup creator
                    result = subprocess.run([
                        sys.executable, 'create_setup_exe.py'
                    ], capture_output=True, text=True, cwd=os.getcwd())
                    
                    progress_bar.stop()
                    progress_dialog.destroy()
                    
                    if result.returncode == 0:
                        # Success - now show setup ready message
                        self.create_setup_installer()
                    else:
                        messagebox.showerror("Setup Failed", f"Failed to create setup installer.\n\nError: {result.stderr}")
                        
                except Exception as e:
                    if 'progress_dialog' in locals():
                        progress_dialog.destroy()
                    messagebox.showerror("Error", f"Setup creation failed: {str(e)}")
            
            # Run build in background thread
            threading.Thread(target=build_process, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start setup creation: {str(e)}")
    
    def show_qr_code(self):
        """Show QR code for current address"""
        self.show_address_qr(self.current_address)
    
    def copy_address(self):
        """Copy address to clipboard"""
        self.root.clipboard_clear()
        self.root.clipboard_append(self.current_address)
        messagebox.showinfo("Copied", "Address copied to clipboard")
    
    def generate_new_address_gui(self):
        """Generate new address with GUI"""
        if not self.wallet_manager.current_wallet:
            messagebox.showerror("Error", "No wallet is currently open")
            return
        
        label = simpledialog.askstring("New Address", "Enter label for new address:")
        if label:
            try:
                new_addr = self.wallet_manager.generate_new_address(label)
                messagebox.showinfo("Success", f"New address generated:\n{new_addr}")
                self.update_displays()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to generate address: {str(e)}")
    
    def open_address_book(self):
        """Open address book"""
        self.show_sending_addresses()
    
    def generate_paper_wallet(self):
        """Generate paper wallet"""
        self.paper_wallet_generator.show_paper_wallet_dialog()

if __name__ == "__main__":
    print("Starting GSC Coin Professional Wallet...")
    wallet = GSCWalletGUI()
    wallet.run()
