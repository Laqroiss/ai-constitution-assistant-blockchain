from web3 import Web3
from dotenv import load_dotenv
import numpy as np
import os

from config import contract_abi

# --- Load environment ---
load_dotenv()
contract_address = os.getenv("CONTRACT_ADDRESS")

# --- Connect to local Ganache ---
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
assert w3.is_connected(), "⚠️ Not connected to Ganache!"

# --- Initialize contract ---
contract = w3.eth.contract(address=contract_address, abi=contract_abi)
w3.eth.default_account = w3.eth.accounts[0]  # first Ganache account

# --- Example embedding ---
embedding = np.random.rand(5)  # example simulated embedding
scaled = [int(x * 100) for x in embedding]

# --- Send vector on-chain ---
tx_hash = contract.functions.storeVector(scaled).transact()
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

print("✅ Stored vector:", scaled)
print("📦 Tx hash:", receipt.transactionHash.hex())
