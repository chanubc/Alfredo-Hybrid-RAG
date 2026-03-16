%%{init: {"theme": "base", "look": "handDrawn", "themeVariables": {"fontFamily": "Comic Sans MS"}}}%%
flowchart TD
    classDef domain fill:#fef3c7,stroke:#d97706,stroke-width:2px,color:#92400e
    classDef app fill:#dcfce7,stroke:#059669,stroke-width:2px,color:#064e3b
    classDef infra fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#1e3a8a
    classDef pres fill:#f3e8ff,stroke:#9333ea,stroke-width:2px,color:#4c1d95

    subgraph Presentation ["1. Presentation Layer (app/api, dashboard)"]
        direction LR
        P1["🌐 FastAPI<br/>(Webhook)"]:::pres
        P2["🖥️ Streamlit<br/>(Dashboard)"]:::pres
        P3["⏰ APScheduler<br/>(Cron)"]:::pres
    end

    subgraph Application ["2. Application Layer (app/application)"]
        direction TB
        A1["⚙️ Services & Agents<br/>(MessageRouter, KnowledgeAgent)"]:::app
        A2["🎯 Use Cases<br/>(SaveLink, Search, Report)"]:::app
        A3["🔌 Outbound Ports<br/>(ScraperPort, AIAnalysisPort)"]:::app
        
        P1 -->|"Trigger"| A1
        P1 -->|"Trigger"| A2
        P2 -->|"Trigger"| A2
        P3 -->|"Trigger"| A2
        
        A1 -->|"Execute"| A2
        A2 -->|"Define needs"| A3
    end

    subgraph Domain ["3. Domain Layer (app/domain)"]
        direction TB
        D1["📦 Entities<br/>(Link, Chunk, User)"]:::domain
        D2["🧠 Domain Rules<br/>(scoring.py, drift.py)"]:::domain
        D3["🔌 Repository Interfaces<br/>(ILinkRepository, etc.)"]:::domain
        
        A2 -->|"Uses"| D3
        A2 -->|"Manipulates"| D1
        A2 -->|"Applies"| D2
        
        A3 -.->|"References"| D1
        D3 -.->|"References"| D1
    end

    subgraph Infrastructure ["4. Infrastructure Layer (app/infrastructure)"]
        direction LR
        I1["🗄️ Repository Adapters<br/>(PostgreSQL)"]:::infra
        I2["📡 External Adapters<br/>(JinaAdapter, OpenAIClient)"]:::infra
    end

    %% Dependency Inversion Principle (The Magic of Clean Architecture)
    I1 -.->|"✨ Implements (Dependency Inversion)"| D3
    I2 -.->|"✨ Implements (Dependency Inversion)"| A3