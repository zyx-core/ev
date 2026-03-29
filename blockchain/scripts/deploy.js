// Deployment script for IEVC-eco smart contracts
const hre = require("hardhat");

async function main() {
    console.log("=".repeat(60));
    console.log("    IEVC-eco Smart Contract Deployment");
    console.log("=".repeat(60));

    const [deployer] = await hre.ethers.getSigners();
    console.log("\nDeploying contracts with account:", deployer.address);
    console.log("Account balance:", (await hre.ethers.provider.getBalance(deployer.address)).toString());

    // Deploy EnergyToken
    console.log("\n[1/3] Deploying EnergyToken...");
    const EnergyToken = await hre.ethers.getContractFactory("EnergyToken");
    const energyToken = await EnergyToken.deploy();
    await energyToken.waitForDeployment();
    const energyTokenAddress = await energyToken.getAddress();
    console.log("    EnergyToken deployed to:", energyTokenAddress);

    // Deploy ChargingRegistry
    console.log("\n[2/3] Deploying ChargingRegistry...");
    const ChargingRegistry = await hre.ethers.getContractFactory("ChargingRegistry");
    const chargingRegistry = await ChargingRegistry.deploy();
    await chargingRegistry.waitForDeployment();
    const registryAddress = await chargingRegistry.getAddress();
    console.log("    ChargingRegistry deployed to:", registryAddress);

    // Deploy TransactionManager
    console.log("\n[3/3] Deploying TransactionManager...");
    const TransactionManager = await hre.ethers.getContractFactory("TransactionManager");
    const transactionManager = await TransactionManager.deploy();
    await transactionManager.waitForDeployment();
    const txManagerAddress = await transactionManager.getAddress();
    console.log("    TransactionManager deployed to:", txManagerAddress);

    console.log("\n" + "=".repeat(60));
    console.log("    Deployment Complete!");
    console.log("=".repeat(60));
    console.log("\nContract Addresses:");
    console.log("  EnergyToken:        ", energyTokenAddress);
    console.log("  ChargingRegistry:   ", registryAddress);
    console.log("  TransactionManager: ", txManagerAddress);
    console.log("\nSave these addresses for backend configuration.");
    console.log("=".repeat(60));

    // Return deployed addresses for verification
    return {
        energyToken: energyTokenAddress,
        chargingRegistry: registryAddress,
        transactionManager: txManagerAddress
    };
}

main()
    .then((addresses) => {
        console.log("\nDeployment successful!");
        process.exit(0);
    })
    .catch((error) => {
        console.error("\nDeployment failed:", error);
        process.exit(1);
    });
