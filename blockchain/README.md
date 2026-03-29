# Blockchain - Smart Contracts

## Overview
Ethereum-based smart contracts for:
- Charging session management
- Automated billing and escrow
- Immutable transaction logging
- EV roaming support

## Tech Stack
- Solidity 0.8.20+
- Hardhat (development framework)
- Ethers.js / Web3.py
- Ganache (local testnet)

## Setup
```bash
cd blockchain
npm install
```

## Contracts (Planned)
- `ChargingRegistry.sol` - Station registry
- `TransactionManager.sol` - Payment escrow and release
- `EnergyToken.sol` - Optional ERC-20 token for payments

## Development
```bash
# Compile contracts
npx hardhat compile

# Run tests
npx hardhat test

# Deploy to local network
npx hardhat node
npx hardhat run scripts/deploy.js --network localhost
```
