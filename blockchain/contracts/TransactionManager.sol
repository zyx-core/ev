// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/**
 * @title TransactionManager
 * @notice Manages charging sessions with escrow payments
 * @dev Handles session lifecycle: start, charge, complete, dispute
 */
contract TransactionManager is Ownable, ReentrancyGuard {
    
    // Session status
    enum SessionStatus { 
        NotStarted,
        Active,        // Charging in progress
        Completed,     // Successfully completed
        Cancelled,     // Cancelled by user
        Disputed,      // Under dispute
        Refunded,      // Payment refunded
        NoShow         // User did not initiate charge; escrow slashed
    }
    
    // Penalty configuration (% of escrow sent to operator on no-show)
    uint256 public noShowPenaltyPercent = 20; // 20% penalty by default
    
    // Charging session structure
    struct ChargingSession {
        string sessionId;           // Unique session ID
        string stationId;           // Reference to station
        address user;               // EV driver address
        address operator;           // CPO address
        uint256 startTime;          // Session start timestamp
        uint256 endTime;            // Session end timestamp
        uint256 reservationExpiry;  // Deadline to begin charging (no-show window)
        uint256 escrowAmount;       // Amount held in escrow (wei)
        uint256 energyDelivered;    // Energy in Wh
        uint256 finalCost;          // Actual cost (wei)
        uint256 ratePerKwh;         // Rate at session start
        SessionStatus status;       // Current status
    }
    
    // Fee configuration
    uint256 public platformFeePercent = 2; // 2% platform fee
    uint256 public constant MAX_FEE = 10;  // Max 10% fee
    
    // Token for payments (optional, 0x0 = ETH)
    IERC20 public paymentToken;
    
    // Storage
    mapping(string => ChargingSession) public sessions;
    mapping(address => string[]) public userSessions;
    mapping(address => string[]) public operatorSessions;
    mapping(address => uint256) public operatorBalances;
    
    // Events
    event SessionStarted(
        string indexed sessionId,
        string indexed stationId,
        address indexed user,
        uint256 escrowAmount,
        uint256 timestamp
    );
    
    event SessionCompleted(
        string indexed sessionId,
        address indexed user,
        uint256 energyDelivered,
        uint256 finalCost,
        uint256 timestamp
    );
    
    event SessionCancelled(
        string indexed sessionId,
        address indexed user,
        uint256 refundAmount
    );
    
    event PaymentReleased(
        string indexed sessionId,
        address indexed operator,
        uint256 amount,
        uint256 platformFee
    );
    
    event DisputeRaised(
        string indexed sessionId,
        address indexed disputer,
        string reason
    );
    
    event DisputeResolved(
        string indexed sessionId,
        uint256 userRefund,
        uint256 operatorPayment
    );
    
    event NoShowSlashed(
        string indexed sessionId,
        address indexed user,
        address indexed operator,
        uint256 penaltyToOperator,
        uint256 refundToUser
    );
    
    constructor() Ownable(msg.sender) {}
    
    /**
     * @notice Start a new charging session with escrow
     * @param _sessionId Unique session ID
     * @param _stationId Station ID
     * @param _operator CPO wallet address
     * @param _ratePerKwh Rate in wei per kWh
     */
    function startSession(
        string calldata _sessionId,
        string calldata _stationId,
        address _operator,
        uint256 _ratePerKwh
    ) external payable nonReentrant {
        require(bytes(_sessionId).length > 0, "Invalid session ID");
        require(sessions[_sessionId].startTime == 0, "Session already exists");
        require(msg.value > 0, "Escrow required");
        require(_operator != address(0), "Invalid operator");
        
        sessions[_sessionId] = ChargingSession({
            sessionId: _sessionId,
            stationId: _stationId,
            user: msg.sender,
            operator: _operator,
            startTime: block.timestamp,
            endTime: 0,
            reservationExpiry: block.timestamp + 15 minutes,
            escrowAmount: msg.value,
            energyDelivered: 0,
            finalCost: 0,
            ratePerKwh: _ratePerKwh,
            status: SessionStatus.Active
        });
        
        userSessions[msg.sender].push(_sessionId);
        operatorSessions[_operator].push(_sessionId);
        
        emit SessionStarted(
            _sessionId,
            _stationId,
            msg.sender,
            msg.value,
            block.timestamp
        );
    }
    
    /**
     * @notice Slash escrow for a no-show reservation (operator only)
     * @dev Callable only after reservationExpiry has passed and session is still Active
     * @param _sessionId Session ID of the expired reservation
     */
    function slashNoShow(string calldata _sessionId) external nonReentrant {
        ChargingSession storage session = sessions[_sessionId];
        
        require(session.startTime > 0, "Session not found");
        require(session.status == SessionStatus.Active, "Session not active");
        require(msg.sender == session.operator, "Only operator can slash");
        require(
            block.timestamp > session.reservationExpiry,
            "Reservation window has not expired yet"
        );
        
        session.status = SessionStatus.NoShow;
        session.endTime = block.timestamp;
        
        // Calculate penalty split
        uint256 penaltyToOperator = (session.escrowAmount * noShowPenaltyPercent) / 100;
        uint256 refundToUser = session.escrowAmount - penaltyToOperator;
        
        // Pay operator penalty
        operatorBalances[session.operator] += penaltyToOperator;
        
        // Refund remainder to user
        if (refundToUser > 0) {
            (bool success, ) = payable(session.user).call{value: refundToUser}("");
            require(success, "User refund failed");
        }
        
        emit NoShowSlashed(
            _sessionId,
            session.user,
            session.operator,
            penaltyToOperator,
            refundToUser
        );
    }
    
    /**
     * @notice Update no-show penalty percentage (admin only)
     * @param _newPercent New penalty percentage (0-50)
     */
    function updateNoShowPenalty(uint256 _newPercent) external onlyOwner {
        require(_newPercent <= 50, "Penalty too high");
        noShowPenaltyPercent = _newPercent;
    }
    
    /**
     * @notice Complete a charging session and release payment
     * @param _sessionId Session ID
     * @param _energyWh Energy delivered in Wh
     */
    function completeSession(
        string calldata _sessionId,
        uint256 _energyWh
    ) external nonReentrant {
        ChargingSession storage session = sessions[_sessionId];
        
        require(session.startTime > 0, "Session not found");
        require(session.status == SessionStatus.Active, "Session not active");
        require(
            msg.sender == session.operator || msg.sender == owner(),
            "Not authorized"
        );
        
        // Calculate final cost
        uint256 energyKwh = _energyWh / 1000; // Convert Wh to kWh
        uint256 finalCost = energyKwh * session.ratePerKwh;
        
        // Cap at escrow amount
        if (finalCost > session.escrowAmount) {
            finalCost = session.escrowAmount;
        }
        
        // Calculate fees
        uint256 platformFee = (finalCost * platformFeePercent) / 100;
        uint256 operatorPayment = finalCost - platformFee;
        uint256 userRefund = session.escrowAmount - finalCost;
        
        // Update session
        session.endTime = block.timestamp;
        session.energyDelivered = _energyWh;
        session.finalCost = finalCost;
        session.status = SessionStatus.Completed;
        
        // Transfer payments
        operatorBalances[session.operator] += operatorPayment;
        
        // Refund excess to user
        if (userRefund > 0) {
            (bool success, ) = payable(session.user).call{value: userRefund}("");
            require(success, "Refund failed");
        }
        
        emit SessionCompleted(
            _sessionId,
            session.user,
            _energyWh,
            finalCost,
            block.timestamp
        );
        
        emit PaymentReleased(
            _sessionId,
            session.operator,
            operatorPayment,
            platformFee
        );
    }
    
    /**
     * @notice Cancel an active session (user only)
     * @param _sessionId Session ID
     */
    function cancelSession(string calldata _sessionId) external nonReentrant {
        ChargingSession storage session = sessions[_sessionId];
        
        require(session.startTime > 0, "Session not found");
        require(session.user == msg.sender, "Not session owner");
        require(session.status == SessionStatus.Active, "Session not active");
        
        // Only allow cancel within first 5 minutes
        require(
            block.timestamp <= session.startTime + 5 minutes,
            "Cancel window expired"
        );
        
        session.status = SessionStatus.Cancelled;
        session.endTime = block.timestamp;
        
        // Full refund
        uint256 refundAmount = session.escrowAmount;
        (bool success, ) = payable(session.user).call{value: refundAmount}("");
        require(success, "Refund failed");
        
        emit SessionCancelled(_sessionId, msg.sender, refundAmount);
    }
    
    /**
     * @notice Raise a dispute for a session
     * @param _sessionId Session ID
     * @param _reason Dispute reason
     */
    function raiseDispute(
        string calldata _sessionId,
        string calldata _reason
    ) external {
        ChargingSession storage session = sessions[_sessionId];
        
        require(session.startTime > 0, "Session not found");
        require(
            msg.sender == session.user || msg.sender == session.operator,
            "Not involved in session"
        );
        require(
            session.status == SessionStatus.Active ||
            session.status == SessionStatus.Completed,
            "Cannot dispute this session"
        );
        
        session.status = SessionStatus.Disputed;
        
        emit DisputeRaised(_sessionId, msg.sender, _reason);
    }
    
    /**
     * @notice Resolve a dispute (admin only)
     * @param _sessionId Session ID
     * @param _userPercent Percentage of escrow to refund user (0-100)
     */
    function resolveDispute(
        string calldata _sessionId,
        uint256 _userPercent
    ) external onlyOwner nonReentrant {
        ChargingSession storage session = sessions[_sessionId];
        
        require(session.status == SessionStatus.Disputed, "Not in dispute");
        require(_userPercent <= 100, "Invalid percentage");
        
        uint256 userRefund = (session.escrowAmount * _userPercent) / 100;
        uint256 operatorPayment = session.escrowAmount - userRefund;
        
        session.status = SessionStatus.Refunded;
        session.endTime = block.timestamp;
        
        if (userRefund > 0) {
            (bool success, ) = payable(session.user).call{value: userRefund}("");
            require(success, "User refund failed");
        }
        
        if (operatorPayment > 0) {
            operatorBalances[session.operator] += operatorPayment;
        }
        
        emit DisputeResolved(_sessionId, userRefund, operatorPayment);
    }
    
    /**
     * @notice Withdraw accumulated earnings (operator)
     */
    function withdrawEarnings() external nonReentrant {
        uint256 balance = operatorBalances[msg.sender];
        require(balance > 0, "No balance to withdraw");
        
        operatorBalances[msg.sender] = 0;
        
        (bool success, ) = payable(msg.sender).call{value: balance}("");
        require(success, "Withdrawal failed");
    }
    
    /**
     * @notice Update platform fee (admin only)
     * @param _newFee New fee percentage
     */
    function updatePlatformFee(uint256 _newFee) external onlyOwner {
        require(_newFee <= MAX_FEE, "Fee too high");
        platformFeePercent = _newFee;
    }
    
    // View functions
    
    function getSession(string calldata _sessionId)
        external
        view
        returns (ChargingSession memory)
    {
        return sessions[_sessionId];
    }
    
    function getUserSessions(address _user)
        external
        view
        returns (string[] memory)
    {
        return userSessions[_user];
    }
    
    function getOperatorBalance(address _operator)
        external
        view
        returns (uint256)
    {
        return operatorBalances[_operator];
    }
    
    function isSessionActive(string calldata _sessionId)
        external
        view
        returns (bool)
    {
        return sessions[_sessionId].status == SessionStatus.Active;
    }
    
    // Allow contract to receive ETH
    receive() external payable {}
}
