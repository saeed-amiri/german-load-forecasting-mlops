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
     │   User Database  │
     │ - Users          │
     │ - Password hashes│
     │ - Roles          │
     │ - Permissions    │
     └──────────────────┘
´´´

##
´´´text
  User  
   │  
   │ 1. POST /login (username, password)  
   ▼  
  Auth Service  
   │  
   │ 2. Validate password (bcrypt)  
   │ 3. Load user + role from DB  
   │ 4. Create JWT with role claim  
   ▼  
  User receives JWT  
   │  
   │ 5. Calls API with:  
   │    Authorization: Bearer <JWT>  
   ▼  
  API Gateway  
   │  
   │ 6. Verify JWT signature  
   │ 7. Check expiration  
   │ 8. Extract role  
   │ 9. Enforce access rules  
   │10. Forward request to backend  
   ▼  
  Backend Service  
   │  
   │11. Trusts gateway  
   │12. Executes business logic  
   │13. Returns response  
   ▼  
  Gateway  
   │  
   │14. Returns response to user  
   ▼  
  User  
´´´