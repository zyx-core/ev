// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title ChargingRegistry
 * @notice Registry for EV charging stations in the IEVC-eco ecosystem
 * @dev Manages station registration, updates, and status tracking
 */
contract ChargingRegistry is Ownable, ReentrancyGuard {
    
    // Station status enum
    enum StationStatus { Inactive, Active, Maintenance, Suspended }
    
    // Connector types
    enum ConnectorType { CCS2, CHAdeMO, Type2, Type1 }
    
    // Station structure
    struct Station {
        string stationId;           // Off-chain station ID (UUID)
        string name;                // Station name
        address operator;           // CPO wallet address
        int256 latitude;            // Latitude * 1e6 (for precision)
        int256 longitude;           // Longitude * 1e6
        uint256 baseRate;           // Base rate in wei per kWh
        uint256 maxPowerKw;         // Maximum power in kW
        StationStatus status;       // Current status
        uint256 totalSessions;      // Total charging sessions
        uint256 totalEnergy;        // Total energy delivered (Wh)
        uint256 registeredAt;       // Registration timestamp
        uint256 updatedAt;          // Last update timestamp
    }
    
    // Connector structure
    struct Connector {
        ConnectorType connectorType;
        uint256 powerKw;
        bool isAvailable;
    }
    
    // Mappings
    mapping(string => Station) public stations;
    mapping(string => Connector[]) public stationConnectors;
    mapping(address => string[]) public operatorStations;
    
    // Events
    event StationRegistered(
        string indexed stationId,
        address indexed operator,
        string name,
        uint256 timestamp
    );
    
    event StationUpdated(
        string indexed stationId,
        StationStatus status,
        uint256 timestamp
    );
    
    event ConnectorAdded(
        string indexed stationId,
        ConnectorType connectorType,
        uint256 powerKw
    );
    
    event StationStatusChanged(
        string indexed stationId,
        StationStatus oldStatus,
        StationStatus newStatus
    );
    
    // Array to track all station IDs
    string[] public stationIds;
    
    constructor() Ownable(msg.sender) {}
    
    /**
     * @notice Register a new charging station
     * @param _stationId Unique station identifier
     * @param _name Station name
     * @param _latitude Latitude * 1e6
     * @param _longitude Longitude * 1e6
     * @param _baseRate Base rate in wei per kWh
     * @param _maxPowerKw Maximum power capacity
     */
    function registerStation(
        string calldata _stationId,
        string calldata _name,
        int256 _latitude,
        int256 _longitude,
        uint256 _baseRate,
        uint256 _maxPowerKw
    ) external nonReentrant {
        require(bytes(_stationId).length > 0, "Invalid station ID");
        require(bytes(stations[_stationId].stationId).length == 0, "Station already exists");
        require(_baseRate > 0, "Base rate must be positive");
        
        stations[_stationId] = Station({
            stationId: _stationId,
            name: _name,
            operator: msg.sender,
            latitude: _latitude,
            longitude: _longitude,
            baseRate: _baseRate,
            maxPowerKw: _maxPowerKw,
            status: StationStatus.Active,
            totalSessions: 0,
            totalEnergy: 0,
            registeredAt: block.timestamp,
            updatedAt: block.timestamp
        });
        
        stationIds.push(_stationId);
        operatorStations[msg.sender].push(_stationId);
        
        emit StationRegistered(_stationId, msg.sender, _name, block.timestamp);
    }
    
    /**
     * @notice Add a connector to a station
     * @param _stationId Station ID
     * @param _connectorType Connector type
     * @param _powerKw Connector power rating
     */
    function addConnector(
        string calldata _stationId,
        ConnectorType _connectorType,
        uint256 _powerKw
    ) external {
        require(bytes(stations[_stationId].stationId).length > 0, "Station not found");
        require(stations[_stationId].operator == msg.sender, "Not station operator");
        
        stationConnectors[_stationId].push(Connector({
            connectorType: _connectorType,
            powerKw: _powerKw,
            isAvailable: true
        }));
        
        emit ConnectorAdded(_stationId, _connectorType, _powerKw);
    }
    
    /**
     * @notice Update station status
     * @param _stationId Station ID
     * @param _newStatus New status
     */
    function updateStationStatus(
        string calldata _stationId,
        StationStatus _newStatus
    ) external {
        require(bytes(stations[_stationId].stationId).length > 0, "Station not found");
        require(
            stations[_stationId].operator == msg.sender || owner() == msg.sender,
            "Not authorized"
        );
        
        StationStatus oldStatus = stations[_stationId].status;
        stations[_stationId].status = _newStatus;
        stations[_stationId].updatedAt = block.timestamp;
        
        emit StationStatusChanged(_stationId, oldStatus, _newStatus);
        emit StationUpdated(_stationId, _newStatus, block.timestamp);
    }
    
    /**
     * @notice Update base rate for a station
     * @param _stationId Station ID
     * @param _newRate New base rate in wei per kWh
     */
    function updateBaseRate(
        string calldata _stationId,
        uint256 _newRate
    ) external {
        require(bytes(stations[_stationId].stationId).length > 0, "Station not found");
        require(stations[_stationId].operator == msg.sender, "Not station operator");
        require(_newRate > 0, "Rate must be positive");
        
        stations[_stationId].baseRate = _newRate;
        stations[_stationId].updatedAt = block.timestamp;
        
        emit StationUpdated(_stationId, stations[_stationId].status, block.timestamp);
    }
    
    /**
     * @notice Record a completed charging session (called by TransactionManager)
     * @param _stationId Station ID
     * @param _energyWh Energy delivered in Wh
     */
    function recordSession(
        string calldata _stationId,
        uint256 _energyWh
    ) external {
        require(bytes(stations[_stationId].stationId).length > 0, "Station not found");
        
        stations[_stationId].totalSessions += 1;
        stations[_stationId].totalEnergy += _energyWh;
    }
    
    // View functions
    
    function getStation(string calldata _stationId) 
        external 
        view 
        returns (Station memory) 
    {
        return stations[_stationId];
    }
    
    function getConnectors(string calldata _stationId)
        external
        view
        returns (Connector[] memory)
    {
        return stationConnectors[_stationId];
    }
    
    function getOperatorStations(address _operator)
        external
        view
        returns (string[] memory)
    {
        return operatorStations[_operator];
    }
    
    function getTotalStations() external view returns (uint256) {
        return stationIds.length;
    }
    
    function isStationActive(string calldata _stationId) 
        external 
        view 
        returns (bool) 
    {
        return stations[_stationId].status == StationStatus.Active;
    }
}
