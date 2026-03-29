"""
Blockchain Service
Web3 integration for smart contract interactions
"""
import os
import json
from typing import Optional
from web3 import Web3
from web3.exceptions import ContractLogicError

# ABI snippets for the contracts (key functions only)
CHARGING_REGISTRY_ABI = [
    {
        "inputs": [
            {"name": "_stationId", "type": "string"},
            {"name": "_name", "type": "string"},
            {"name": "_latitude", "type": "int256"},
            {"name": "_longitude", "type": "int256"},
            {"name": "_baseRate", "type": "uint256"},
            {"name": "_maxPowerKw", "type": "uint256"}
        ],
        "name": "registerStation",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "_stationId", "type": "string"}],
        "name": "getStation",
        "outputs": [
            {
                "components": [
                    {"name": "stationId", "type": "string"},
                    {"name": "name", "type": "string"},
                    {"name": "operator", "type": "address"},
                    {"name": "latitude", "type": "int256"},
                    {"name": "longitude", "type": "int256"},
                    {"name": "baseRate", "type": "uint256"},
                    {"name": "maxPowerKw", "type": "uint256"},
                    {"name": "status", "type": "uint8"},
                    {"name": "totalSessions", "type": "uint256"},
                    {"name": "totalEnergy", "type": "uint256"},
                    {"name": "registeredAt", "type": "uint256"},
                    {"name": "updatedAt", "type": "uint256"}
                ],
                "type": "tuple"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "_stationId", "type": "string"}],
        "name": "isStationActive",
        "outputs": [{"type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "_stationId", "type": "string"},
            {"name": "_energyWh", "type": "uint256"}
        ],
        "name": "recordSession",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

TRANSACTION_MANAGER_ABI = [
    {
        "inputs": [
            {"name": "_sessionId", "type": "string"},
            {"name": "_stationId", "type": "string"},
            {"name": "_operator", "type": "address"},
            {"name": "_ratePerKwh", "type": "uint256"}
        ],
        "name": "startSession",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {"name": "_sessionId", "type": "string"},
            {"name": "_energyWh", "type": "uint256"}
        ],
        "name": "completeSession",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "_sessionId", "type": "string"}],
        "name": "cancelSession",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"name": "_sessionId", "type": "string"}],
        "name": "getSession",
        "outputs": [
            {
                "components": [
                    {"name": "sessionId", "type": "string"},
                    {"name": "stationId", "type": "string"},
                    {"name": "user", "type": "address"},
                    {"name": "operator", "type": "address"},
                    {"name": "startTime", "type": "uint256"},
                    {"name": "endTime", "type": "uint256"},
                    {"name": "escrowAmount", "type": "uint256"},
                    {"name": "energyDelivered", "type": "uint256"},
                    {"name": "finalCost", "type": "uint256"},
                    {"name": "ratePerKwh", "type": "uint256"},
                    {"name": "status", "type": "uint8"}
                ],
                "type": "tuple"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "_sessionId", "type": "string"}],
        "name": "isSessionActive",
        "outputs": [{"type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    }
]


class BlockchainService:
    """
    Service for interacting with IEVC-eco smart contracts
    """
    
    def __init__(
        self,
        provider_url: str = "http://127.0.0.1:8545",
        registry_address: Optional[str] = None,
        transaction_manager_address: Optional[str] = None,
        private_key: Optional[str] = None
    ):
        """
        Initialize blockchain service
        
        Args:
            provider_url: Ethereum node URL (default: local Hardhat)
            registry_address: ChargingRegistry contract address
            transaction_manager_address: TransactionManager contract address
            private_key: Private key for signing transactions
        """
        self.w3 = Web3(Web3.HTTPProvider(provider_url))
        self.private_key = private_key or os.getenv("BLOCKCHAIN_PRIVATE_KEY")
        
        # Load contract addresses from environment or parameters
        self.registry_address = registry_address or os.getenv("REGISTRY_CONTRACT_ADDRESS")
        self.tx_manager_address = transaction_manager_address or os.getenv("TX_MANAGER_CONTRACT_ADDRESS")
        
        # Initialize contracts if addresses are available
        self.registry_contract = None
        self.tx_manager_contract = None
        
        if self.registry_address:
            self.registry_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.registry_address),
                abi=CHARGING_REGISTRY_ABI
            )
        
        if self.tx_manager_address:
            self.tx_manager_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.tx_manager_address),
                abi=TRANSACTION_MANAGER_ABI
            )
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to blockchain"""
        try:
            return self.w3.is_connected()
        except Exception:
            return False
    
    @property
    def account(self) -> Optional[str]:
        """Get account address from private key"""
        if self.private_key:
            return self.w3.eth.account.from_key(self.private_key).address
        return None
    
    def _send_transaction(self, tx_func, value: int = 0) -> str:
        """
        Build and send a transaction
        
        Returns:
            Transaction hash as hex string
        """
        if not self.private_key:
            raise ValueError("Private key required for transactions")
        
        account = self.w3.eth.account.from_key(self.private_key)
        
        # Build transaction
        tx = tx_func.build_transaction({
            'from': account.address,
            'nonce': self.w3.eth.get_transaction_count(account.address),
            'gas': 500000,
            'gasPrice': self.w3.eth.gas_price,
            'value': value
        })
        
        # Sign and send
        signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        # Wait for receipt
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return tx_hash.hex()
    
    # ChargingRegistry functions
    
    def register_station(
        self,
        station_id: str,
        name: str,
        latitude: float,
        longitude: float,
        base_rate_wei: int,
        max_power_kw: int
    ) -> str:
        """
        Register a new station on the blockchain
        
        Returns:
            Transaction hash
        """
        if not self.registry_contract:
            raise ValueError("Registry contract not configured")
        
        # Convert lat/lng to fixed-point (multiply by 1e6)
        lat_fixed = int(latitude * 1e6)
        lng_fixed = int(longitude * 1e6)
        
        tx_func = self.registry_contract.functions.registerStation(
            station_id,
            name,
            lat_fixed,
            lng_fixed,
            base_rate_wei,
            max_power_kw
        )
        
        return self._send_transaction(tx_func)
    
    def get_station(self, station_id: str) -> Optional[dict]:
        """Get station data from blockchain"""
        if not self.registry_contract:
            return None
        
        try:
            result = self.registry_contract.functions.getStation(station_id).call()
            return {
                'station_id': result[0],
                'name': result[1],
                'operator': result[2],
                'latitude': result[3] / 1e6,
                'longitude': result[4] / 1e6,
                'base_rate_wei': result[5],
                'max_power_kw': result[6],
                'status': result[7],
                'total_sessions': result[8],
                'total_energy': result[9],
                'registered_at': result[10],
                'updated_at': result[11]
            }
        except Exception as e:
            print(f"Error getting station: {e}")
            return None
    
    def is_station_registered(self, station_id: str) -> bool:
        """Check if station is registered on blockchain"""
        if not self.registry_contract:
            return False
        
        try:
            return self.registry_contract.functions.isStationActive(station_id).call()
        except Exception:
            return False
    
    def record_session(self, station_id: str, energy_wh: int) -> str:
        """Record a completed session on the blockchain"""
        if not self.registry_contract:
            raise ValueError("Registry contract not configured")
        
        tx_func = self.registry_contract.functions.recordSession(station_id, energy_wh)
        return self._send_transaction(tx_func)
    
    # TransactionManager functions
    
    def start_blockchain_session(
        self,
        session_id: str,
        station_id: str,
        operator_address: str,
        rate_per_kwh_wei: int,
        escrow_amount_wei: int
    ) -> str:
        """
        Start a charging session with escrow on blockchain
        
        Returns:
            Transaction hash
        """
        if not self.tx_manager_contract:
            raise ValueError("TransactionManager contract not configured")
        
        tx_func = self.tx_manager_contract.functions.startSession(
            session_id,
            station_id,
            Web3.to_checksum_address(operator_address),
            rate_per_kwh_wei
        )
        
        return self._send_transaction(tx_func, value=escrow_amount_wei)
    
    def complete_blockchain_session(self, session_id: str, energy_wh: int) -> str:
        """Complete a session and release payment"""
        if not self.tx_manager_contract:
            raise ValueError("TransactionManager contract not configured")
        
        tx_func = self.tx_manager_contract.functions.completeSession(
            session_id,
            energy_wh
        )
        
        return self._send_transaction(tx_func)
    
    def cancel_blockchain_session(self, session_id: str) -> str:
        """Cancel a session and refund escrow"""
        if not self.tx_manager_contract:
            raise ValueError("TransactionManager contract not configured")
        
        tx_func = self.tx_manager_contract.functions.cancelSession(session_id)
        return self._send_transaction(tx_func)
    
    def get_blockchain_session(self, session_id: str) -> Optional[dict]:
        """Get session data from blockchain"""
        if not self.tx_manager_contract:
            return None
        
        try:
            result = self.tx_manager_contract.functions.getSession(session_id).call()
            return {
                'session_id': result[0],
                'station_id': result[1],
                'user': result[2],
                'operator': result[3],
                'start_time': result[4],
                'end_time': result[5],
                'escrow_amount': result[6],
                'energy_delivered': result[7],
                'final_cost': result[8],
                'rate_per_kwh': result[9],
                'status': result[10]
            }
        except Exception as e:
            print(f"Error getting session: {e}")
            return None


# Singleton instance
_blockchain_service: Optional[BlockchainService] = None


def get_blockchain_service() -> BlockchainService:
    """Get or create blockchain service instance"""
    global _blockchain_service
    
    if _blockchain_service is None:
        _blockchain_service = BlockchainService()
    
    return _blockchain_service


def init_blockchain_service(
    provider_url: str = "http://127.0.0.1:8545",
    registry_address: Optional[str] = None,
    transaction_manager_address: Optional[str] = None,
    private_key: Optional[str] = None
) -> BlockchainService:
    """Initialize blockchain service with custom config"""
    global _blockchain_service
    
    _blockchain_service = BlockchainService(
        provider_url=provider_url,
        registry_address=registry_address,
        transaction_manager_address=transaction_manager_address,
        private_key=private_key
    )
    
    return _blockchain_service
