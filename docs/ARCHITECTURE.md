# BetBudAI Project Architecture (v2.0)

## Overview

BetBudAI is a high-performance AI-powered horse racing picks platform rebuilt with modular architecture for maintainability and scalability.

**Live**: https://www.betbudai.com  
**Backend API**: https://mnybvagd5m.execute-api.eu-west-1.amazonaws.com  
**Region**: AWS eu-west-1 (Ireland)

## Key Improvements from v1.0

### Modularity
- ✅ **Separated concerns**: Scoring, settlement, enrichment, agentic AI in distinct modules
- ✅ **Modular API routes**: Picks, results, auth, admin in separate Flask blueprints
- ✅ **No code duplication**: Single source of truth per component (no more `_bpapi_patched.py`)
- ✅ **Modular frontend**: Pages and components instead of monolithic App.js

### Performance
- ✅ **Dynamic configuration**: Weights loaded from DynamoDB with hot-reload (5min cache)
- ✅ **Caching layer**: Unified cache strategy for ROI, picks, results
- ✅ **Async processing**: Step Functions pipelines with parallel agent execution
- ✅ **Database optimization**: Proper indexing and query patterns

### Observability
- ✅ **Structured logging**: JSON format for CloudWatch Insights
- ✅ **Distributed tracing**: X-Ray integration for Lambda calls
- ✅ **Custom metrics**: CloudWatch metrics per pipeline stage
- ✅ **Health checks**: Dedicated health endpoints

### Testing
- ✅ **Unit tests**: Scoring signals, settlement logic, API routes
- ✅ **Integration tests**: Pipeline steps, external API mocks
- ✅ **CI/CD pipeline**: GitHub Actions for automated testing/deployment

## Architecture

### Backend Structure
```
backend/
├── core/                    # Core business logic
│   ├── scoring/            # 7-factor scoring engine + 50+ signals
│   ├── settlement/         # Result settlement & P&L calculation
│   ├── enrichment/         # Data enrichment (Betfair, SL, Racing API, etc)
│   └── agentic/            # Agentic AI orchestration + specialist agents
├── api/                     # REST API (replaces monolithic lambda)
│   ├── routes/             # Modular Flask blueprints
│   │   ├── picks_routes.py       # GET /api/picks/*
│   │   ├── results_routes.py     # GET /api/results/*
│   │   ├── auth_routes.py        # POST /api/auth/*
│   │   └── admin_routes.py       # /api/admin/*
│   ├── middleware/         # Auth, CORS, logging
│   ├── models/             # Request/response schemas (Pydantic)
│   └── app.py              # Main Flask app
├── pipeline/               # Step Functions Lambda handlers
│   ├── morning/            # Betfair fetch + analysis (08:30 UTC)
│   ├── refresh/            # Validation + featured meeting (12:00, 14:00, etc)
│   ├── evening/            # Results fetch + settlement (20:00 UTC)
│   ├── learning/           # Weight optimization (nightly)
│   └── deploy.py           # Deployment orchestrator
├── config/                 # Configuration management
│   ├── weights.py          # Dynamic weight loading + hot-reload
│   ├── secrets.py          # AWS Secrets Manager integration
│   └── settings.py         # Environment-specific config
├── database/               # DynamoDB helpers
│   ├── models.py           # Item schemas (Pydantic)
│   ├── repository.py       # CRUD operations
│   └── migrations/         # Schema migrations
├── external/               # External API clients
│   ├── betfair.py          # Betfair Exchange API
│   ├── sporting_life.py    # Sporting Life scraper
│   ├── racing_api.py       # Racing API client
│   └── ourhub.py           # OurHub API client
├── utils/                  # Utilities
│   ├── logger.py           # Structured logging
│   ├── monitoring.py       # CloudWatch metrics
│   └── cache.py            # Unified caching
├── tests/                  # Test suites
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── fixtures/           # Test data
└── requirements.txt        # Python dependencies
```

### Frontend Structure
```
frontend/
├── src/
│   ├── pages/              # Route-level pages
│   │   ├── HomePage.jsx
│   │   ├── PicksPage.jsx
│   │   ├── ResultsPage.jsx
│   │   ├── FeaturedPage.jsx
│   │   ├── LayTheFavPage.jsx
│   │   ├── MajorRacesPage.jsx
│   │   ├── AdminPage.jsx
│   │   └── SubscriptionPage.jsx
│   ├── components/         # Reusable components
│   │   ├── common/         # Shared UI (Header, Footer, etc)
│   │   ├── picks/          # Pick card components
│   │   ├── results/        # Result display components
│   │   ├── auth/           # Login, register forms
│   │   └── admin/          # Admin-only components
│   ├── hooks/              # React hooks
│   │   ├── useAuth.js      # Auth state management
│   │   ├── useCache.js     # Cache management
│   │   └── usePicks.js     # Picks data fetching
│   ├── services/           # API clients & utilities
│   │   ├── api.js          # Axios instance + request helpers
│   │   ├── auth.js         # Auth service
│   │   └── cache.js        # Local storage cache
│   ├── styles/             # CSS modules & theme
│   │   ├── index.css
│   │   └── variables.css
│   ├── App.jsx             # Main router
│   └── index.js            # Entry point
├── public/                 # Static assets
├── package.json
└── .env.example
```

### Infrastructure
```
infrastructure/
├── lambda/                 # Lambda function definitions
├── dynamodb/               # DynamoDB tables & GSIs
├── iam/                    # IAM roles & policies
├── step_functions/         # State machine definitions
│   ├── morning_sm.json
│   ├── refresh_sm.json
│   ├── evening_sm.json
│   └── learning_sm.json
├── api_gateway.tf          # API Gateway configuration
├── cloudwatch.tf           # CloudWatch alarms & dashboards
├── eventbridge.tf          # EventBridge rules & schedules
└── main.tf                 # Main infrastructure
```

## Data Flow

### Morning Pipeline (08:30 UTC)
1. **Fetch Betfair**: Get racing markets for next 24h (surebet-betfair-fetch)
2. **Run Analysis**: 7-factor scoring on all horses (surebet-analysis)
3. **Select Picks**: Top 5 official + 2 watchlist (comprehensive_pick_logic)
4. **Validate**: Sanity checks before publishing (surebet-validate)
5. **Notify**: Email/SMS to subscribers (surebet-notify)

### Refresh Pipeline (12:00, 14:00, 16:00, 18:00 UTC)
1. **Validate Picks**: Ensure still valid (prices, fields)
2. **Featured Meeting**: Analyze featured course for the day
3. **Cache ROI**: Pre-compute ROI for fast UI loading

### Evening Pipeline (20:00 UTC)
1. **Fetch Results**: Sporting Life fast-results (surebet-sl-results)
2. **Fetch Betfair**: Market settlement prices (surebet-betfair-results)
3. **Reconcile**: Match picks to results, calculate P&L
4. **Generate Reports**: Loss analysis for next-day learning
5. **Cache Results**: Pre-compute strike rates & summaries

### Learning Pipeline (22:00 UTC daily)
1. **Analyze Performance**: Last 7 days of picks vs results
2. **Calculate Signal Deltas**: Which weights are performing?
3. **Optimize Weights**: Adjust using gradient descent (surebet-learning)
4. **Save Weights**: Store in DynamoDB for morning reload

## Key Learnings from Live Operation

### Settlement & Results
- **Offset matching**: Race times must match exactly (UTC, not local)
- **Pre-race guard**: Never settle a pick before race_start_time
- **Authoritative source**: Sporting Life fast-results is ~10-30min ahead of Betfair
- **Winner reconciliation**: Exact horse name/number matching required

### Scoring Signals
- **Form signals**: Last-run win + consistency are top predictors
- **Going & ground**: Heavy going is highly unpredictable (-12 pts penalty)
- **Market position**: Model top pick sometimes weaker than market favourite (needs penalty)
- **Large fields**: 16+ runners reduce discrimination (-10 to -18 pts)
- **Trainer combos**: Trainer reputation + hot form simultaneously = strongest signal
- **Young improvers**: Lightly-raced 4-5yos with improving form (odds 4-10) represent hidden upside
- **Timeform ratings**: 5-star ratings are gold-standard signal (even free from SL)

### Race Types & Venues
- **AW evening races**: Wolverhampton after 17:30 = high variance, need discount (-12 pts)
- **Irish handicaps**: Curragh/Dundalk/Navan/Naas = competitive, tight weights, unpredictable pace
- **Class drops**: Horse dropping from Class 2/3 to 4/5 = quality ceiling above field (+12 bonus)
- **Same trainer rivals**: If trainer has 2+ in same race, attention is split (-10 pts per horse)

## APIs & Integrations

### External Services
- **Betfair Exchange**: Live odds, market settlement (certificate auth)
- **Sporting Life**: Racecards, form, results (web scraping)
- **Racing API**: Basic racecards, race classification (HTTP Basic auth)
- **OurHub**: Trainer/jockey win rates, confirmed going (API)
- **AWS Secrets Manager**: Credentials, API keys (rotated)
- **AWS SES**: Email notifications to subscribers
- **AWS SNS**: SMS alerts (future)

### DynamoDB Tables
- **SureBetBets**: Picks/bets/results (pk: bet_date, sk: bet_id)
- **BetBudAI_Subscribers**: User accounts (pk: email, gsi: email_verified, username_reserved)
- **SureBetAgentJobs**: Agentic AI execution logs (TTL: 90 days)
- **SureBetConfig**: Weights, settings, locks (pk: bet_id='CONFIG', sk: bet_date='SYSTEM_WEIGHTS')

## Deployment

### Local Development
```bash
cd BetBudAI
docker-compose up      # Backend + LocalStack for testing
cd frontend && npm start  # Frontend dev server
```

### AWS Deployment
```bash
cd backend/pipeline
python deploy.py       # Deploy all Lambdas and Step Functions
# Verify in CloudWatch/Lambda console
```

### Frontend Deployment
- AWS Amplify auto-deploys from `frontend/` branch changes
- Manual: `cd frontend && npm run build && aws s3 sync build/ s3://betbudai-frontend/`

## Monitoring

### CloudWatch Dashboards
- Pipeline execution times (Morning, Refresh, Evening, Learning)
- Pick coverage, strike rate trends
- API latency, error rates
- Lambda cold starts

### Alarms
- Pipeline failures (SNS notification)
- High error rate on /api/* endpoints
- DynamoDB throttling
- Agentic AI agent failures

## Next Steps (Roadmap)

1. ✅ Modular architecture (v2.0 - THIS REBUILD)
2. ⏳ Complete unit & integration tests
3. ⏳ GitHub Actions CI/CD pipeline
4. ⏳ Stripe payment integration (already coded, needs wiring)
5. ⏳ User subscription tiers (free/pro/vip)
6. ⏳ Advanced analytics dashboard
7. ⏳ Multi-sport expansion (greyhounds, darts, football, rugby)

## References

- [API Documentation](./API.md)
- [Deployment Guide](./DEPLOYMENT.md)
- [Operational Learnings](./LEARNINGS.md)
- [Troubleshooting](./TROUBLESHOOTING.md)
