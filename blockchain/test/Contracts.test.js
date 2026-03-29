const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("ChargingRegistry", function () {
    let registry;
    let owner, operator, user;

    const stationId = "station-001";
    const stationName = "Downtown Fast Charger";
    const latitude = 12970000; // 12.97 * 1e6
    const longitude = 77590000; // 77.59 * 1e6
    const baseRate = ethers.parseEther("0.001"); // 0.001 ETH per kWh
    const maxPower = 150; // 150 kW

    beforeEach(async function () {
        [owner, operator, user] = await ethers.getSigners();

        const ChargingRegistry = await ethers.getContractFactory("ChargingRegistry");
        registry = await ChargingRegistry.deploy();
        await registry.waitForDeployment();
    });

    describe("Station Registration", function () {
        it("Should register a new station", async function () {
            await registry.connect(operator).registerStation(
                stationId, stationName, latitude, longitude, baseRate, maxPower
            );

            const station = await registry.getStation(stationId);
            expect(station.name).to.equal(stationName);
            expect(station.operator).to.equal(operator.address);
            expect(station.status).to.equal(1); // Active
        });

        it("Should emit StationRegistered event", async function () {
            await expect(
                registry.connect(operator).registerStation(
                    stationId, stationName, latitude, longitude, baseRate, maxPower
                )
            ).to.emit(registry, "StationRegistered")
                .withArgs(stationId, operator.address, stationName, await getBlockTimestamp());
        });

        it("Should not allow duplicate station IDs", async function () {
            await registry.connect(operator).registerStation(
                stationId, stationName, latitude, longitude, baseRate, maxPower
            );

            await expect(
                registry.connect(operator).registerStation(
                    stationId, "Another Station", latitude, longitude, baseRate, maxPower
                )
            ).to.be.revertedWith("Station already exists");
        });
    });

    describe("Connector Management", function () {
        beforeEach(async function () {
            await registry.connect(operator).registerStation(
                stationId, stationName, latitude, longitude, baseRate, maxPower
            );
        });

        it("Should add connector to station", async function () {
            await registry.connect(operator).addConnector(stationId, 0, 150); // CCS2, 150kW

            const connectors = await registry.getConnectors(stationId);
            expect(connectors.length).to.equal(1);
            expect(connectors[0].powerKw).to.equal(150);
        });

        it("Should only allow operator to add connectors", async function () {
            await expect(
                registry.connect(user).addConnector(stationId, 0, 150)
            ).to.be.revertedWith("Not station operator");
        });
    });

    describe("Status Updates", function () {
        beforeEach(async function () {
            await registry.connect(operator).registerStation(
                stationId, stationName, latitude, longitude, baseRate, maxPower
            );
        });

        it("Should update station status", async function () {
            await registry.connect(operator).updateStationStatus(stationId, 2); // Maintenance

            const station = await registry.getStation(stationId);
            expect(station.status).to.equal(2);
        });

        it("Should check if station is active", async function () {
            expect(await registry.isStationActive(stationId)).to.be.true;

            await registry.connect(operator).updateStationStatus(stationId, 0); // Inactive
            expect(await registry.isStationActive(stationId)).to.be.false;
        });
    });
});

describe("TransactionManager", function () {
    let txManager;
    let owner, operator, user;

    const sessionId = "session-001";
    const stationId = "station-001";
    const ratePerKwh = ethers.parseEther("0.001");
    const escrowAmount = ethers.parseEther("1.0");

    beforeEach(async function () {
        [owner, operator, user] = await ethers.getSigners();

        const TransactionManager = await ethers.getContractFactory("TransactionManager");
        txManager = await TransactionManager.deploy();
        await txManager.waitForDeployment();
    });

    describe("Session Management", function () {
        it("Should start a new session with escrow", async function () {
            await txManager.connect(user).startSession(
                sessionId, stationId, operator.address, ratePerKwh,
                { value: escrowAmount }
            );

            const session = await txManager.getSession(sessionId);
            expect(session.user).to.equal(user.address);
            expect(session.escrowAmount).to.equal(escrowAmount);
            expect(session.status).to.equal(1); // Active
        });

        it("Should emit SessionStarted event", async function () {
            await expect(
                txManager.connect(user).startSession(
                    sessionId, stationId, operator.address, ratePerKwh,
                    { value: escrowAmount }
                )
            ).to.emit(txManager, "SessionStarted");
        });

        it("Should require escrow", async function () {
            await expect(
                txManager.connect(user).startSession(
                    sessionId, stationId, operator.address, ratePerKwh,
                    { value: 0 }
                )
            ).to.be.revertedWith("Escrow required");
        });
    });

    describe("Session Completion", function () {
        beforeEach(async function () {
            await txManager.connect(user).startSession(
                sessionId, stationId, operator.address, ratePerKwh,
                { value: escrowAmount }
            );
        });

        it("Should complete session and calculate payment", async function () {
            const energyWh = 50000; // 50 kWh

            await txManager.connect(operator).completeSession(sessionId, energyWh);

            const session = await txManager.getSession(sessionId);
            expect(session.status).to.equal(2); // Completed
            expect(session.energyDelivered).to.equal(energyWh);
        });

        it("Should credit operator balance", async function () {
            const energyWh = 50000;

            await txManager.connect(operator).completeSession(sessionId, energyWh);

            const balance = await txManager.getOperatorBalance(operator.address);
            expect(balance).to.be.gt(0);
        });
    });

    describe("Withdrawals", function () {
        it("Should allow operator to withdraw earnings", async function () {
            // Start and complete a session
            await txManager.connect(user).startSession(
                sessionId, stationId, operator.address, ratePerKwh,
                { value: escrowAmount }
            );
            await txManager.connect(operator).completeSession(sessionId, 100000);

            const balanceBefore = await ethers.provider.getBalance(operator.address);
            await txManager.connect(operator).withdrawEarnings();
            const balanceAfter = await ethers.provider.getBalance(operator.address);

            expect(balanceAfter).to.be.gt(balanceBefore);
        });
    });
});

describe("EnergyToken", function () {
    let token;
    let owner, minter, user;

    beforeEach(async function () {
        [owner, minter, user] = await ethers.getSigners();

        const EnergyToken = await ethers.getContractFactory("EnergyToken");
        token = await EnergyToken.deploy();
        await token.waitForDeployment();
    });

    describe("Token Basics", function () {
        it("Should have correct name and symbol", async function () {
            expect(await token.name()).to.equal("IEVC Energy Token");
            expect(await token.symbol()).to.equal("IEVC");
        });

        it("Should mint initial supply to deployer", async function () {
            const initialSupply = ethers.parseEther("100000000"); // 100M
            expect(await token.balanceOf(owner.address)).to.equal(initialSupply);
        });
    });

    describe("Minting", function () {
        it("Should allow minter to mint tokens", async function () {
            const amount = ethers.parseEther("1000");
            await token.connect(owner).mint(user.address, amount);

            expect(await token.balanceOf(user.address)).to.equal(amount);
        });

        it("Should not exceed max supply", async function () {
            const tooMuch = ethers.parseEther("1000000000"); // 1B (exceeds remaining)

            await expect(
                token.connect(owner).mint(user.address, tooMuch)
            ).to.be.revertedWith("Exceeds max supply");
        });
    });

    describe("Rewards", function () {
        it("Should issue charging rewards", async function () {
            await token.connect(owner).issueChargingReward(user.address, 100); // 100 kWh

            const balance = await token.balanceOf(user.address);
            expect(balance).to.equal(ethers.parseEther("100")); // 1 token per kWh
        });

        it("Should issue referral rewards", async function () {
            await token.connect(owner).issueReferralReward(user.address);

            const balance = await token.balanceOf(user.address);
            expect(balance).to.equal(ethers.parseEther("10")); // 10 tokens per referral
        });
    });
});

// Helper function to get current block timestamp
async function getBlockTimestamp() {
    const block = await ethers.provider.getBlock("latest");
    return block.timestamp;
}
