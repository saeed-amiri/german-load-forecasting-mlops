´´´text

                   ┌──────────────────────────┐
                   │        Frontend          │
                   │  (UI, CLI, API client)   │
                   └─────────────┬────────────┘
                                 │
                                 ▼
                     ┌──────────────────────┐
                     │      API Gateway     │
                     │  - Verify JWT        │
                     │  - Enforce roles     │
                     │  - Route requests    │
                     └──────────┬───────────┘
                                │
        ┌───────────────────────┼────────────────────────┐
        │                       │                        │
        ▼                       ▼                        ▼
    ┌───────────────────┐   ┌──────────────────┐    ┌──────────────────┐
    │   Auth Service    │   │   Backend A      │    │   Backend B      │
    │ - Login           │   │ - Business logic │    │ - Business logic │
    │ - Password check  │   │ - No auth logic  │    │ - No auth logic  │
    │ - JWT creation    │   │ - Trust gateway  │    │ - Trust gateway  │
    └─────────┬─────────┘   └──────────────────┘    └──────────────────┘
              │
              ▼
     ┌──────────────────┐
     │   User Database   │
     │ - Users           │
     │ - Password hashes │
     │ - Roles           │
     │ - Permissions     │
     └──────────────────┘
´´´