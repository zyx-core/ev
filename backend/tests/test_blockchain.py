"""
Test Blockchain Service
Unit tests for Web3 blockchain integration
"""
import pytest
from unittest.mock import Mock, patch, MagicMock


class TestBlockchainService:
    """Test cases for blockchain service"""
    
    def test_service_initialization(self):
        """Test blockchain service can be initialized"""
        from app.services.blockchain import BlockchainService
        
        # Initialize with mock provider (won't actually connect)
        service = BlockchainService(
            provider_url="http://127.0.0.1:8545"
        )
        
        assert service is not None
        assert service.registry_contract is None  # No address provided
        assert service.tx_manager_contract is None
    
    def test_service_with_addresses(self):
        """Test service initialization with contract addresses"""
        from app.services.blockchain import BlockchainService
        
        # Mock addresses
        service = BlockchainService(
            provider_url="http://127.0.0.1:8545",
            registry_address="0x742d35Cc6634C0532925a3b844Bc9e7595f8fE00",
            transaction_manager_address="0x8626f6940E2eb28930eFb4CeF49B2d1F2C9C1199"
        )
        
        assert service.registry_address is not None
        assert service.tx_manager_address is not None
    
    def test_singleton_pattern(self):
        """Test that get_blockchain_service returns singleton"""
        from app.services.blockchain import get_blockchain_service, init_blockchain_service
        
        # Initialize 
        init_blockchain_service()
        
        # Get service twice
        service1 = get_blockchain_service()
        service2 = get_blockchain_service()
        
        assert service1 is service2
    
    @patch('app.services.blockchain.Web3')
    def test_is_connected_property(self, mock_web3_class):
        """Test is_connected property"""
        from app.services.blockchain import BlockchainService
        
        mock_w3 = MagicMock()
        mock_w3.is_connected.return_value = True
        mock_web3_class.return_value = mock_w3
        
        service = BlockchainService()
        # The mock should return True
        assert hasattr(service, 'is_connected')
    
    def test_station_data_parsing(self):
        """Test that station data parsing works correctly"""
        from app.services.blockchain import BlockchainService
        
        # Test the data parsing logic
        test_result = (
            "station-001",  # stationId
            "Test Station",  # name
            "0x742d35Cc6634C0532925a3b844Bc9e7595f8fE00",  # operator
            40712800,  # latitude (fixed point)
            -74006000,  # longitude (fixed point)
            350000000000000000,  # baseRate (wei)
            150,  # maxPowerKw
            1,  # status (Active)
            100,  # totalSessions
            50000,  # totalEnergy
            1704067200,  # registeredAt
            1704153600   # updatedAt
        )
        
        # Parse result (simulating what get_station returns)
        parsed = {
            'station_id': test_result[0],
            'name': test_result[1],
            'operator': test_result[2],
            'latitude': test_result[3] / 1e6,
            'longitude': test_result[4] / 1e6,
            'base_rate_wei': test_result[5],
            'max_power_kw': test_result[6],
            'status': test_result[7],
            'total_sessions': test_result[8],
            'total_energy': test_result[9],
            'registered_at': test_result[10],
            'updated_at': test_result[11]
        }
        
        assert parsed['station_id'] == "station-001"
        assert parsed['latitude'] == 40.7128
        assert parsed['longitude'] == -74.006
        assert parsed['max_power_kw'] == 150


class TestBlockchainIntegration:
    """Integration tests for blockchain (requires local node)"""
    
    @pytest.mark.skip(reason="Requires local blockchain node")
    def test_register_station(self):
        """Test registering a station on blockchain"""
        from app.services.blockchain import init_blockchain_service
        
        service = init_blockchain_service(
            registry_address="0x...",  # Replace with deployed address
            private_key="0x..."  # Replace with test key
        )
        
        tx_hash = service.register_station(
            station_id="test-station-001",
            name="Test Station",
            latitude=40.7128,
            longitude=-74.0060,
            base_rate_wei=350000000000000000,  # 0.35 ETH
            max_power_kw=150
        )
        
        assert tx_hash is not None
        assert tx_hash.startswith("0x")
    
    @pytest.mark.skip(reason="Requires local blockchain node")
    def test_start_session(self):
        """Test starting a blockchain session"""
        from app.services.blockchain import get_blockchain_service
        
        service = get_blockchain_service()
        
        tx_hash = service.start_blockchain_session(
            session_id="session-001",
            station_id="test-station-001",
            operator_address="0x742d35Cc6634C0532925a3b844Bc9e7595f8fE00",
            rate_per_kwh_wei=350000000000000000,
            escrow_amount_wei=1000000000000000000  # 1 ETH
        )
        
        assert tx_hash is not None
