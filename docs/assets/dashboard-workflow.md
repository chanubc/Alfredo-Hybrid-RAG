%%{init: {"theme": "base", "look": "handDrawn", "themeVariables": {"fontFamily": "Comic Sans MS"}}}%%
flowchart TD
    classDef user fill:#dbeafe,stroke:#0284c7,color:#1e3a8a
    classDef interface fill:#ccfbf1,stroke:#0d9488,color:#115e59
    classDef router fill:#f3e8ff,stroke:#9333ea,color:#4c1d95
    classDef usecase fill:#dcfce7,stroke:#22c55e,color:#14532d
    classDef storage fill:#fed7aa,stroke:#f97316,color:#7c2d12
    classDef external fill:#ffe4e6,stroke:#e11d48,color:#881337

    %% 1. Input Layer
    A1["👤 Telegram User<br/>(via Magic Link)"]:::user
    A2["⏰ Scheduler<br/>(Cron)"]:::interface
    
    %% 2. Interface / Router Layer
    B1["🖥️ Streamlit Dashboard"]:::interface
    B2["AuthService<br/>(Verify JWT)"]:::router
    
    %% 3. UseCase Layer
    C1["Library / Insights UseCase"]:::usecase
    C2["GenerateWeeklyReport UseCase"]:::usecase
    
    %% 4. Storage & External Layer
    D[("🗄️ PostgreSQL<br/>(DB)")]:::storage
    E1["🤖 OpenAI API<br/>(Generate Briefing)"]:::external
    E2["📱 Telegram API<br/>(Push Notification)"]:::external

    %% Dashboard Flow
    A1 -.->|"Click URL"| B1
    B1 -->|"1. Extract Token"| B2
    B2 -->|"2. Validate"| C1
    C1 -->|"3. Fetch Data"| D
    
    %% Scheduler Flow
    A2 --> C2
    C2 -->|"1. Fetch Drift & Links"| D
    C2 -.->|"2. Summarize"| E1
    C2 -.->|"3. Push Report"| E2