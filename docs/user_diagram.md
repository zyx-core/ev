# IEVC-eco User Diagram

## System Actors & Interactions

```mermaid
graph TB
    subgraph Users["👥 Users"]
        EVD["🚗 EV Driver"]
        CPO["🏢 Charging Point Operator"]
        GA["⚡ Grid Aggregator"]
    end

    subgraph Frontend["📱 Frontend Layer"]
        FLUTTER["Flutter Mobile App"]
        REACT["React Dashboard"]
    end

    subgraph Backend["🖥️ Backend Services"]
        API["FastAPI Server"]
        MCDM["MCDM Recommendation Engine"]
        DB[(SQLite Database)]
    end

    subgraph AI["🧠 AI/ML Layer"]
        FL["Federated Learning Server"]
        LSTM["Battery Prediction Model"]
        MARL["Multi-Agent RL Engine"]
    end

    subgraph Blockchain["🔗 Blockchain Layer"]
        SC["Smart Contracts"]
        BILLING["Billing & Payments"]
        RESERVE["Reservation Management"]
    end

    subgraph External["🌐 External Systems"]
        CS["Charging Stations"]
        GRID["Power Grid"]
    end

    %% EV Driver Flows
    EVD -->|"Find charging stations"| FLUTTER
    EVD -->|"View recommendations"| FLUTTER
    EVD -->|"Make reservations"| FLUTTER
    EVD -->|"Pay for charging"| FLUTTER

    %% CPO Flows
    CPO -->|"Monitor stations"| REACT
    CPO -->|"Set pricing"| REACT
    CPO -->|"View analytics"| REACT

    %% Grid Aggregator Flows
    GA -->|"Predict demand"| REACT
    GA -->|"Manage load"| REACT

    %% Frontend to Backend
    FLUTTER -->|"REST API"| API
    REACT -->|"REST API"| API

    %% Backend Internal
    API --> MCDM
    API --> DB
    MCDM -->|"Station ranking"| API

    %% AI Connections
    API -->|"Battery SoC data"| FL
    FL --> LSTM
    LSTM -->|"Predictions"| API
    MARL -->|"Dynamic pricing"| API
    MARL -->|"Load balancing"| API

    %% Blockchain Connections
    API -->|"Transactions"| SC
    SC --> BILLING
    SC --> RESERVE
    BILLING -->|"Payment confirmation"| API
    RESERVE -->|"Slot booking"| API

    %% External Systems
    API <-->|"OCPP 2.0.1"| CS
    MARL <-->|"Grid signals"| GRID
```

---

## User Journey Flows

### 🚗 EV Driver Journey
```mermaid
sequenceDiagram
    participant D as EV Driver
    participant App as Mobile App
    participant API as Backend API
    participant ML as ML Engine
    participant BC as Blockchain

    D->>App: Open app & share location
    App->>API: Request recommendations
    API->>ML: Get battery predictions
    ML-->>API: Return SoC forecast
    API-->>App: Ranked station list
    App-->>D: Display options

    D->>App: Select station & time slot
    App->>API: Create reservation
    API->>BC: Record on blockchain
    BC-->>API: Transaction hash
    API-->>App: Confirmation
    App-->>D: Booking confirmed

    D->>App: Complete charging session
    App->>API: End session
    API->>BC: Process payment
    BC-->>API: Payment verified
    API-->>App: Receipt
    App-->>D: Session complete
```

### 🏢 CPO Dashboard Flow
```mermaid
sequenceDiagram
    participant O as Operator
    participant Dash as React Dashboard
    participant API as Backend API
    participant MARL as MARL Engine

    O->>Dash: Login to dashboard
    Dash->>API: Fetch station status
    API-->>Dash: Station data
    Dash-->>O: Display overview

    O->>Dash: Update pricing strategy
    Dash->>API: Submit new rates
    API->>MARL: Optimize pricing
    MARL-->>API: Suggested multipliers
    API-->>Dash: Updated pricing
    Dash-->>O: Confirm changes
```

---

## Data Flow Summary

| Actor | Actions | Data Exchanged |
|-------|---------|----------------|
| **EV Driver** | Find stations, Reserve slots, Pay | Location, Battery SoC, Payment info |
| **CPO** | Manage stations, Set prices, Analytics | Station status, Revenue, Usage patterns |
| **Grid Aggregator** | Predict demand, Balance load | Energy forecasts, Grid signals |

