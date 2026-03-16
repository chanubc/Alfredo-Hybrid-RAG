%%{init: {"theme": "base", "look": "handDrawn", "themeVariables": {"fontFamily": "Comic Sans MS"}}}%%
flowchart TD
    classDef user fill:#dbeafe,stroke:#0284c7,color:#1e3a8a
    classDef interface fill:#ccfbf1,stroke:#0d9488,color:#115e59
    classDef router fill:#f3e8ff,stroke:#9333ea,color:#4c1d95
    classDef usecase fill:#dcfce7,stroke:#22c55e,color:#14532d
    classDef storage fill:#fed7aa,stroke:#f97316,color:#7c2d12
    classDef external fill:#ffe4e6,stroke:#e11d48,color:#881337

    %% 1. Input Layer
    A["👤 Telegram User"]:::user
    B["📱 Telegram Bot API"]:::interface
    
    %% 2. Router Layer
    C["TelegramWebhookHandler"]:::router
    D["MessageRouterService<br/>(+ IntentClassifier)"]:::router
    
    %% 3. UseCase & Auth Layer
    E1["SaveLink UseCase"]:::usecase
    E2["SaveMemo UseCase"]:::usecase
    E3["Search UseCase"]:::usecase
    E4["KnowledgeAgent<br/>(Ask Flow)"]:::usecase
    E5["AuthService<br/>(Magic Link 생성)"]:::router
    
    %% 4. RAG & Storage Layer
    F["HybridRetriever"]:::usecase
    G[("🗄️ PostgreSQL<br/>(DB & Vector)")]:::storage
    
    %% 5. External API Layer
    H1["🧪 Jina Reader"]:::external
    H2["🤖 OpenAI API<br/>(Embed/Analyze/Chat)"]:::external
    H3["📜 Notion API<br/>(Sync)"]:::external
    
    %% 6. Output Layer
    I["💬 Telegram Response<br/>(Answer or Web Link)"]:::user

    %% 핵심 흐름
    A --> B --> C --> D
    
    %% 분기 처리 (Dashboard 추가)
    D -->|"URL"| E1
    D -->|"Memo"| E2
    D -->|"SEARCH"| E3
    D -->|"ASK"| E4
    D -->|"DASHBOARD"| E5
    
    %% Save Flow
    E1 -.->|"1. Scrape"| H1
    E1 -.->|"2. Analyze & Embed"| H2
    E1 -->|"3. Save"| G
    E1 -.->|"4. Sync"| H3
    
    E2 -.->|"1. Embed"| H2
    E2 -->|"2. Save"| G
    E2 -.->|"3. Sync"| H3
    
    %% Search & Ask Flow
    E3 --> F
    E4 --> F
    F -.->|"Embed Query"| H2
    F -->|"Search"| G
    E4 -.->|"Chat / Tool Call"| H2
    
    %% Response Flow
    E5 -->|"Generate JWT URL"| I
    G --> I