// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";

/**
 * @title EnergyToken
 * @notice ERC-20 token for IEVC-eco ecosystem payments
 * @dev IEVC token for charging payments, rewards, and incentives
 */
contract EnergyToken is ERC20, ERC20Burnable, AccessControl {
    
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");
    bytes32 public constant OPERATOR_ROLE = keccak256("OPERATOR_ROLE");
    
    // Token economics
    uint256 public constant MAX_SUPPLY = 1_000_000_000 * 10**18; // 1 billion tokens
    uint256 public constant INITIAL_SUPPLY = 100_000_000 * 10**18; // 100 million initial
    
    // Reward rates (tokens per kWh)
    uint256 public chargeRewardRate = 1 * 10**18; // 1 token per kWh for charging
    uint256 public referralRewardRate = 10 * 10**18; // 10 tokens per referral
    
    // Events
    event RewardIssued(
        address indexed recipient,
        uint256 amount,
        string rewardType
    );
    
    event RewardRateUpdated(
        string rateType,
        uint256 oldRate,
        uint256 newRate
    );
    
    constructor() ERC20("IEVC Energy Token", "IEVC") {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(MINTER_ROLE, msg.sender);
        _grantRole(OPERATOR_ROLE, msg.sender);
        
        // Mint initial supply to deployer
        _mint(msg.sender, INITIAL_SUPPLY);
    }
    
    /**
     * @notice Mint new tokens (minter only)
     * @param to Recipient address
     * @param amount Amount to mint
     */
    function mint(address to, uint256 amount) external onlyRole(MINTER_ROLE) {
        require(totalSupply() + amount <= MAX_SUPPLY, "Exceeds max supply");
        _mint(to, amount);
    }
    
    /**
     * @notice Issue charging reward
     * @param recipient User address
     * @param energyKwh Energy charged in kWh
     */
    function issueChargingReward(
        address recipient,
        uint256 energyKwh
    ) external onlyRole(OPERATOR_ROLE) {
        uint256 reward = energyKwh * chargeRewardRate;
        require(totalSupply() + reward <= MAX_SUPPLY, "Exceeds max supply");
        
        _mint(recipient, reward);
        emit RewardIssued(recipient, reward, "charging");
    }
    
    /**
     * @notice Issue referral reward
     * @param referrer Address of referrer
     */
    function issueReferralReward(
        address referrer
    ) external onlyRole(OPERATOR_ROLE) {
        require(totalSupply() + referralRewardRate <= MAX_SUPPLY, "Exceeds max supply");
        
        _mint(referrer, referralRewardRate);
        emit RewardIssued(referrer, referralRewardRate, "referral");
    }
    
    /**
     * @notice Issue custom reward
     * @param recipient Recipient address
     * @param amount Reward amount
     * @param rewardType Type of reward
     */
    function issueReward(
        address recipient,
        uint256 amount,
        string calldata rewardType
    ) external onlyRole(OPERATOR_ROLE) {
        require(totalSupply() + amount <= MAX_SUPPLY, "Exceeds max supply");
        
        _mint(recipient, amount);
        emit RewardIssued(recipient, amount, rewardType);
    }
    
    /**
     * @notice Update charging reward rate (admin only)
     * @param newRate New rate in tokens per kWh
     */
    function updateChargeRewardRate(
        uint256 newRate
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        uint256 oldRate = chargeRewardRate;
        chargeRewardRate = newRate;
        emit RewardRateUpdated("charging", oldRate, newRate);
    }
    
    /**
     * @notice Update referral reward rate (admin only)
     * @param newRate New referral reward amount
     */
    function updateReferralRewardRate(
        uint256 newRate
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        uint256 oldRate = referralRewardRate;
        referralRewardRate = newRate;
        emit RewardRateUpdated("referral", oldRate, newRate);
    }
    
    /**
     * @notice Add minter role to address
     * @param account Address to grant minter role
     */
    function addMinter(address account) external onlyRole(DEFAULT_ADMIN_ROLE) {
        grantRole(MINTER_ROLE, account);
    }
    
    /**
     * @notice Add operator role to address
     * @param account Address to grant operator role
     */
    function addOperator(address account) external onlyRole(DEFAULT_ADMIN_ROLE) {
        grantRole(OPERATOR_ROLE, account);
    }
    
    /**
     * @notice Get remaining mintable supply
     */
    function remainingMintableSupply() external view returns (uint256) {
        return MAX_SUPPLY - totalSupply();
    }
}
