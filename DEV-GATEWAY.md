´´´  

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
´´´  

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


STEP 0 — Create the Auth Service Folder Structure  
  
This is the foundation.  
  
Goal:    
Create the skeleton under services/auth/ and docker/auth/.  
  
This gives you a place to put identity logic.  
STEP 1 — Implement Password Hashing  
  
Before you can authenticate anyone, you need secure password storage.  
  
Goal:    
Add hashing.py with bcrypt hashing + verification.  
  
This ensures your user DB is safe.  
STEP 2 — Implement User Database Access  
  
Your auth service must read users from a real DB.  
  
Goal:    
Add database.py + models.py to load users and roles.  
  
This is where your real user table lives.  
STEP 3 — Implement JWT Creation  
  
Now that you can validate a user, you can issue tokens.  
  
Goal:    
Add jwt_utils.py to create signed JWTs with:  
  
    sub (user id)  
  
    role  
  
    exp  
  
This is the identity token your gateway will trust.  
STEP 4 — Implement the Login Route  
  
This is the first real endpoint.  
  
Goal:    
Add /auth/login in routes/login.py:  
  
    Accept username/password  
  
    Validate against DB  
  
    Return JWT  
  
This is the entrypoint for all authentication.  
STEP 5 — Implement Optional User Routes  
  
Optional but realistic.  
  
Goal:    
Add /auth/register, /auth/me, etc.  
  
This makes your auth service feel like a real identity provider.  
STEP 6 — Build the Auth Service Docker Image  
  
Your project uses a separate docker/ folder.  
  
Goal:    
Add docker/auth/Dockerfile + requirements.txt.  
  
This makes the auth service deployable.  
STEP 7 — Add Auth Service to docker-compose  
  
Now your system becomes multi-service.  
  
Goal:    
Expose auth service on port 8002 (or similar).  
  
This allows the gateway to call it.  
STEP 8 — Update Gateway to Verify JWT  
  
Your gateway becomes a real API gateway.  
  
Goal:    
Add JWT verification middleware in deployment/gateway/.  
  
This enforces authentication.  
STEP 9 — Add Role-Based Access Control (RBAC)  
  
Now your gateway enforces permissions.  
  
Goal:    
Check payload["role"] inside gateway routes.  
  
This is where your system becomes secure.  
STEP 10 — Connect Gateway → Auth Service  
  
This is the final integration.  
  
Goal:    
Gateway forwards /login to auth service  
Backend receives identity via headers  
  
This completes the architecture.  