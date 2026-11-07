<div align="center">

# 🧠 AI Trends Intelligence Platform

### *The Command Center for Global AI Intelligence*

<br/>

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-AI-6366F1?style=for-the-badge&logo=openai&logoColor=white)](https://openrouter.ai)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)
[![PM2](https://img.shields.io/badge/PM2-Production-2B037A?style=for-the-badge&logo=pm2&logoColor=white)](https://pm2.keymetrics.io/)
[![RSS](https://img.shields.io/badge/RSS_Feeds-80+-F97316?style=for-the-badge&logo=rss&logoColor=white)](#-rss-intelligence-network-80-sources)

<br/>

> **A production-grade, AI-powered intelligence platform that aggregates, analyzes, scores, and publishes global AI trends from 80+ premium sources — powered by a multi-agent AI system, real-time RSS aggregation, and automated cross-platform publishing.**

<br/>

<img src="https://img.shields.io/badge/⚡_Real--Time_RSS_Aggregation-0EA5E9?style=flat-square&logoColor=white" alt="RSS"/>
<img src="https://img.shields.io/badge/🤖_Multi--Agent_AI_System-8B5CF6?style=flat-square&logoColor=white" alt="AI"/>
<img src="https://img.shields.io/badge/🔒_Enterprise_Security-10B981?style=flat-square&logoColor=white" alt="Security"/>
<img src="https://img.shields.io/badge/📡_Auto--Publishing-F59E0B?style=flat-square&logoColor=white" alt="Publishing"/>
<img src="https://img.shields.io/badge/🔍_AI_Search_Engine-EF4444?style=flat-square&logoColor=white" alt="Search"/>
<img src="https://img.shields.io/badge/📊_Trend_Scoring-6366F1?style=flat-square&logoColor=white" alt="Scoring"/>

</div>

---

## 📖 Table of Contents

- [✨ Why This Exists](#-why-this-exists)
- [🎯 Key Features](#-key-features)
- [🏗 System Architecture](#-system-architecture)
- [📦 Project Structure](#-project-structure)
- [🤖 Multi-Agent AI System](#-multi-agent-ai-system)
- [📡 RSS Intelligence Network (80+ Sources)](#-rss-intelligence-network-80-sources)
- [🔐 Enterprise Security Model](#-enterprise-security-model)
- [🚀 Quick Start](#-quick-start)
- [⚙️ Configuration](#️-configuration)
- [🖥 PM2 Production Deployment](#-pm2-production-deployment)
- [📱 UI & Pages](#-ui--pages)
- [🔌 API Reference](#-api-reference)
- [🧩 Extensibility](#-extensibility)
- [🗺 Roadmap](#-roadmap)
- [📄 License](#-license)

---

## ✨ Why This Exists

The AI landscape moves at **lightspeed**. New models, breakthroughs, tools, and startups emerge *every single day*. Keeping track is impossible.

**AI Trends Intelligence Platform** solves this by:

| Problem | Solution |
|---|---|
| 🌊 Information overload from hundreds of AI sources | 📥 Automated RSS aggregation from **80+ curated feeds** |
| 🤷 No way to know what's actually important | 🏆 AI-powered **trend scoring (0-100)** with categorization |
| ⏰ Manual content creation is time-consuming | ✍️ AI agents generate **platform-optimized** social content |
| 🔍 Hard to search across all AI news efficiently | 🧠 **Perplexity-style** AI search engine over your data |
| 📤 Publishing to multiple platforms is tedious | 🚀 **One-click multi-platform** publishing (Twitter, LinkedIn, Reddit) |
| 🖼 Missing visuals for social posts | 🎨 **AI image generation** (FLUX.2) for every trend |
| 🔔 Missing critical developments | 📲 **Telegram bot** notifications for high-scoring trends |

---

## 🎯 Key Features

<table>
<tr>
<td width="50%">

### 📥 Intelligent RSS Aggregation
- **80+ premium AI sources** monitored continuously
- Concurrent fetching with 8 parallel workers
- SHA-256 deduplication across all feeds
- Auto-retry with exponential backoff
- Configurable fetch intervals & article limits

</td>
<td width="50%">

### 🤖 Multi-Agent AI System
- **5 specialized AI agents** working in concert
- Trend scoring with 0-100 confidence scale
- Auto-categorization into 12+ categories
- Platform-optimized content generation
- AI-powered image creation with FLUX.2

</td>
</tr>
<tr>
<td width="50%">

### 🔍 AI-Powered Search
- Perplexity-style natural language search
- Searches across all stored trends & articles
- Context-aware AI responses with citations
- Search result caching for performance
- Real-time search suggestions

</td>
<td width="50%">

### 📤 Cross-Platform Publishing
- **Twitter/X** — optimized thread generation
- **LinkedIn** — professional long-form posts
- **Reddit** — subreddit-targeted content
- Scheduling queue with status tracking
- Full publish history & analytics

</td>
</tr>
<tr>
<td width="50%">

### 🔒 Enterprise Security
- JWT access + refresh token authentication
- Bcrypt password hashing with salt
- Rate limiting per route & per user
- CSRF protection + security headers
- Fernet-encrypted sensitive data storage
- Comprehensive audit logging

</td>
<td width="50%">

### 📊 Admin Dashboard
- Real-time platform statistics
- User management (CRUD + role assignment)
- Feed management (add/edit/disable/delete)
- Publishing queue management
- System health monitoring
- Audit log viewer

</td>
</tr>
</table>

---

## 🏗 System Architecture

```
╔══════════════════════════════════════════════════════════════════════════╗
║                    🧠 AI TRENDS INTELLIGENCE PLATFORM                  ║
╠══════════════════════════════════════════════════════════════════════════╣
║                                                                        ║
║  ┌──────────────────── PRESENTATION LAYER ────────────────────────┐    ║
║  │  🌐 Jinja2 Templates │ 📱 Responsive UI │ ⚡ Real-time Updates │    ║
║  │  Landing │ Dashboard │ Trends │ Search │ Publish │ Admin       │    ║
║  └────────────────────────────┬───────────────────────────────────┘    ║
║                               │                                        ║
║  ┌──────────────────── ROUTE LAYER (Blueprints) ─────────────────┐    ║
║  │  🔐 auth_routes  │  📈 trend_routes   │  🔍 search_routes    │    ║
║  │  📤 publish_routes│  👑 admin_routes   │  📄 page_routes      │    ║
║  └────────────────────────────┬───────────────────────────────────┘    ║
║                               │                                        ║
║  ┌──────────────────── SERVICE LAYER ────────────────────────────┐    ║
║  │                                                                │    ║
║  │  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐    │    ║
║  │  │ 📡 RSS      │  │ 📤 Publisher │  │ 📲 Telegram Bot   │    │    ║
║  │  │ Engine      │  │  Service     │  │  Notifications    │    │    ║
║  │  │ (8 workers) │  │ (multi-plat) │  │  (real-time)      │    │    ║
║  │  └─────────────┘  └──────────────┘  └───────────────────┘    │    ║
║  │                                                                │    ║
║  │  ┌──────────────────────────────────────────────────────┐     │    ║
║  │  │ ⏰ APScheduler — Background Job Orchestration        │     │    ║
║  │  │  • Feed Refresh (every 30 min)                       │     │    ║
║  │  │  • Article Analysis (every 35 min)                   │     │    ║
║  │  │  • Publish Queue Processing (every 15 min)           │     │    ║
║  │  └──────────────────────────────────────────────────────┘     │    ║
║  └────────────────────────────┬───────────────────────────────────┘    ║
║                               │                                        ║
║  ┌──────────────────── MULTI-AGENT AI SYSTEM ────────────────────┐    ║
║  │                                                                │    ║
║  │  ┌──────────┐ ┌──────────┐ ┌─────────┐ ┌────────┐ ┌───────┐  │    ║
║  │  │ 📊 Trend │ │ ✍️ Content│ │ 🎨 Image│ │ #️⃣ Hash│ │ 🔬 Re-│  │    ║
║  │  │  Analyst │ │  Writer  │ │ Creator │ │  tag   │ │ search│  │    ║
║  │  │  Agent   │ │  Agent   │ │  Agent  │ │ Agent  │ │ Agent │  │    ║
║  │  └────┬─────┘ └────┬─────┘ └────┬────┘ └───┬────┘ └───┬───┘  │    ║
║  │       └────────────┴────────────┴───────────┴───────────┘      │    ║
║  │                    ┌────────────────┐                          │    ║
║  │                    │ 🔗 OpenRouter  │                          │    ║
║  │                    │  API Gateway   │                          │    ║
║  │                    │ (Gemini/FLUX)  │                          │    ║
║  │                    └────────────────┘                          │    ║
║  └────────────────────────────┬───────────────────────────────────┘    ║
║                               │                                        ║
║  ┌──────────────────── DATA LAYER ───────────────────────────────┐    ║
║  │  📁 Thread-safe JSON Store │ 🔐 Fernet Encryption │ 📋 Audit │    ║
║  │  articles.json │ trends.json │ users.json │ tokens.json       │    ║
║  └───────────────────────────────────────────────────────────────┘    ║
║                                                                        ║
║  ┌──────────────────── SECURITY LAYER ───────────────────────────┐    ║
║  │  🔑 JWT Auth │ 🧂 Bcrypt │ 🚦 Rate Limit │ 🛡 CSRF │ 🧹 XSS │    ║
║  │  HSTS │ CSP │ X-Frame │ Token Revocation │ Audit Logging      │    ║
║  └───────────────────────────────────────────────────────────────┘    ║
║                                                                        ║
╚══════════════════════════════════════════════════════════════════════════╝
```

---

## 📦 Project Structure

```
ai-trends-intelligence/
│
├── 🚀 app.py                     # Flask app factory & entry point
├── ⚙️ config.py                   # Configuration from environment variables
├── 📋 requirements.txt            # Python dependencies
├── 🔧 ecosystem.config.js         # PM2 production configuration
├── 📖 README.md                   # You are here!
├── 🚫 .gitignore                  # Git ignore rules
│
├── 🤖 agents/                     # Multi-Agent AI System
│   ├── openrouter_client.py       # OpenRouter API gateway (LLM + Image)
│   ├── trend_agent.py             # Trend scoring (0-100) & categorization
│   ├── content_agent.py           # Platform-optimized content generation
│   ├── image_agent.py             # FLUX.2 AI image generation
│   ├── hashtag_agent.py           # Intelligent hashtag generation
│   └── search_agent.py            # Perplexity-style AI search
│
├── 📁 data/                       # Data persistence layer
│   └── store.py                   # Thread-safe JSON CRUD + Fernet encryption
│
├── 🔐 security/                   # Security module
│   ├── auth.py                    # JWT auth, bcrypt, decorators
│   └── validation.py              # Input validation & HTML sanitization
│
├── ⚙️ services/                    # Business logic services
│   ├── rss_engine.py              # RSS fetcher (80+ feeds, 8 workers)
│   ├── publisher.py               # Multi-platform publishing engine
│   ├── telegram_bot.py            # Telegram admin notifications
│   └── scheduler.py               # APScheduler background jobs
│
├── 🛣 routes/                      # Flask blueprints (API endpoints)
│   ├── auth_routes.py             # /api/auth/* (login, register, refresh)
│   ├── trend_routes.py            # /api/trends/* (CRUD, scoring, analysis)
│   ├── search_routes.py           # /api/search/* (AI-powered search)
│   ├── publish_routes.py          # /api/publish/* (queue, publish, history)
│   ├── admin_routes.py            # /api/admin/* (users, feeds, stats)
│   └── page_routes.py             # HTML page routes
│
├── 🎨 templates/                   # Jinja2 HTML templates
│   ├── base.html                  # Base layout with shared assets
│   ├── index.html                 # Landing page
│   ├── login.html                 # Authentication page
│   ├── register.html              # Registration page
│   ├── dashboard.html             # Main analytics dashboard
│   ├── trends.html                # Trends explorer & management
│   ├── articles.html              # Articles browser
│   ├── search.html                # AI search interface
│   ├── publish.html               # Publishing hub
│   ├── settings.html              # User settings & preferences
│   ├── admin.html                 # Admin control panel
│   └── components/
│       └── sidebar.html           # Sidebar navigation component
│
└── 🎭 static/                     # Static assets
    ├── css/
    │   └── styles.css             # Complete design system (2000+ lines)
    └── js/
        ├── api.js                 # API client with JWT management
        └── app.js                 # UI controller & page logic
```

---

## 🤖 Multi-Agent AI System

The platform uses a **5-agent architecture** where each agent is a specialized AI worker powered by OpenRouter models:

```
                    ┌─────────────────────────┐
                    │      📰 New Article      │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   📊 TREND ANALYST       │
                    │   ──────────────────     │
                    │   • Scores 0-100         │
                    │   • Categorizes          │
                    │   • Detects duplicates   │
                    │   • Extracts key themes  │
                    └────────────┬────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                   │
   ┌──────────▼─────┐ ┌────────▼────────┐ ┌───────▼────────┐
   │ ✍️ CONTENT      │ │ 🎨 IMAGE        │ │ #️⃣ HASHTAG      │
   │  WRITER         │ │  CREATOR        │ │  INTELLIGENCE   │
   │  ────────────   │ │  ────────────   │ │  ────────────   │
   │  • Twitter/X    │ │  • FLUX.2 model │ │  • Platform-    │
   │  • LinkedIn     │ │  • Custom       │ │    specific     │
   │  • Reddit       │ │    prompts      │ │  • Trending     │
   │  • Blog format  │ │  • Auto-save    │ │    analysis     │
   └─────────────────┘ └─────────────────┘ └────────────────┘
              │                  │                   │
              └──────────────────┼──────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   📤 PUBLISH QUEUE       │
                    │   ──────────────────     │
                    │   Ready for multi-       │
                    │   platform publishing    │
                    └─────────────────────────┘


   ┌─────────────────────────────────────────────────┐
   │  🔬 RESEARCH AGENT (Independent)                 │
   │  ────────────────────────────────                │
   │  • Perplexity-style search                       │
   │  • Natural language queries                      │
   │  • Searches across all stored data               │
   │  • AI-synthesized answers with citations         │
   └─────────────────────────────────────────────────┘
```

### Agent Details

| Agent | Model | Purpose | Output |
|-------|-------|---------|--------|
| 📊 **Trend Analyst** | Gemini 2.0 Flash | Scores articles 0-100, categorizes, detects duplicates | Trend score, category, themes, summary |
| ✍️ **Content Writer** | Gemini 2.0 Flash | Generates platform-optimized social media posts | Twitter threads, LinkedIn posts, Reddit posts |
| 🎨 **Image Creator** | FLUX.2 Pro | Creates AI-generated visuals for trends | High-res images saved to disk |
| #️⃣ **Hashtag Intel** | Gemini 2.0 Flash | Generates platform-specific hashtag sets | Optimized hashtags per platform |
| 🔬 **Research Agent** | Gemini 2.0 Flash | Perplexity-style search over stored trends | AI-synthesized answers with sources |

---

## 📡 RSS Intelligence Network (80+ Sources)

The platform monitors **80+ premium RSS feeds** across **12 categories**, making it one of the most comprehensive AI news aggregators available:

<table>
<tr>
<td width="50%">

### 🔬 Core AI Labs (20)
- MIT Technology Review
- OpenAI Blog
- Google AI Blog
- DeepMind Blog
- Anthropic Blog
- Hugging Face Blog
- Papers With Code
- The Batch (Andrew Ng)
- Microsoft AI Blog
- AWS Machine Learning
- NVIDIA AI Blog
- Meta AI Blog
- Stability AI, Cohere, Mistral
- AI21 Labs, Together AI
- Apple ML Research
- Salesforce AI Research
- Allen AI (AI2)

</td>
<td width="50%">

### 📰 AI Industry News (15)
- VentureBeat AI
- TechCrunch AI
- The Verge AI
- Wired AI
- ZDNet AI
- AI News
- Unite.AI
- SiliconAngle AI
- AI Business
- Forbes AI
- The Register AI
- CIO AI
- TechRadar AI
- Ars Technica
- *...and more*

</td>
</tr>
<tr>
<td width="50%">

### 📚 Research & Academic (15)
- Towards Data Science
- Synced Review
- Import AI Newsletter
- Singularity Hub
- Machine Learning Mastery
- KDnuggets
- InfoQ AI/ML
- arXiv (CS.AI, CS.LG, CS.CL, CS.CV)
- Distill.pub
- Sebastian Raschka Blog
- Last Week in AI
- Analytics India Magazine

</td>
<td width="50%">

### 📬 Newsletters & Curated (7)
- The Neuron
- Ben's Bites
- Superhuman AI
- AI Tool Report
- TLDR AI
- The Rundown AI
- Latent Space Podcast

### 🛡 AI Security (2)
- The Hacker News
- Dark Reading AI

### 🛠 Developer Tools (9)
- GitHub Blog
- Dev.to (AI, ML, LLM)
- Hacker News AI
- Product Hunt AI
- Ollama, LangChain, LlamaIndex

</td>
</tr>
<tr>
<td width="50%">

### ⚖️ Ethics & Policy (4)
- AI Ethics Brief
- Future of Life Institute
- OECD AI Policy
- Brookings AI Policy

### 🤖 Robotics (3)
- IEEE Spectrum Robotics
- TechCrunch Robotics
- The Robot Report

</td>
<td width="50%">

### 🏥 AI Healthcare (2)
- Nature Machine Intelligence
- Healthcare IT News AI

### ☁️ Cloud & Enterprise (4)
- Google Cloud AI
- Azure AI Blog
- IBM AI Blog
- Oracle AI Blog

### 🎨 AI Creative (3)
- Runway ML, ElevenLabs, Midjourney

### 💰 AI Funding (3)
- AI Fund, CB Insights AI, Y Combinator

</td>
</tr>
</table>

---

## 🔐 Enterprise Security Model

Security is not an afterthought — it's built into every layer:

```
┌─────────────────────────────────────────────────────────┐
│                    REQUEST LIFECYCLE                      │
│                                                          │
│  Client ──▶ Rate Limiter ──▶ CSRF Check ──▶ JWT Auth    │
│     │                                          │         │
│     │         ┌────────────────────────────────┘         │
│     │         ▼                                          │
│     │    Input Validation ──▶ Business Logic             │
│     │                              │                     │
│     │         ┌────────────────────┘                     │
│     │         ▼                                          │
│     │    Audit Logging ──▶ Security Headers ──▶ Response │
│     │                                              │     │
│     ◀──────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

| Layer | Implementation | Details |
|-------|---------------|---------|
| 🔑 **Authentication** | JWT access + refresh tokens | Automatic rotation, configurable expiry |
| 🧂 **Password Storage** | bcrypt with salt | Industry-standard hashing |
| 🚦 **Rate Limiting** | flask-limiter | `100/hour` default, `20/min` for auth |
| 🛡 **CSRF Protection** | X-CSRF-Token header | Validated on all state-changing requests |
| 📋 **Security Headers** | HSTS, CSP, X-Frame-Options | Defense against XSS, clickjacking, MIME sniffing |
| 🔐 **Data Encryption** | Fernet symmetric encryption | For sensitive JSON fields |
| 📝 **Audit Logging** | Append-only daily logs | Full traceability of all actions |
| 👑 **Role Separation** | `admin_required` decorator | Strict admin/user role enforcement |
| 🚫 **Token Revocation** | JTI-based blacklisting | Instant session invalidation |
| 🧹 **Input Sanitization** | bleach + custom validators | HTML stripping + server-side validation |

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Node.js 18+** (for PM2)
- **PM2** (`npm install -g pm2`)

### 1️⃣ Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/ai-trends-intelligence.git
cd ai-trends-intelligence
```

### 2️⃣ Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate    # Linux/macOS
# venv\Scripts\activate     # Windows
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Configure environment

```bash
cp .env.example .env
```

Edit `.env` with your actual keys:

```ini
# 🔑 Required
FLASK_SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_hex(32))">
JWT_SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_hex(32))">
OPENROUTER_API_KEY=<your-openrouter-api-key>

# 📲 Optional — Telegram Notifications
TELEGRAM_BOT_TOKEN=<from @BotFather>
TELEGRAM_ADMIN_CHAT_ID=<your-chat-id>
TELEGRAM_ENABLED=true

# 📤 Optional — Social Publishing
PUBLISH_TWITTER_ENABLED=false
PUBLISH_LINKEDIN_ENABLED=false
PUBLISH_REDDIT_ENABLED=false
```

### 5️⃣ Run the application

```bash
# Development
python app.py

# Production (with PM2)
pm2 start ecosystem.config.js
pm2 save
```

### 6️⃣ Open in browser

```
🌐 http://localhost:5000
```

### 🔑 Default Admin Account

| Field | Value |
|-------|-------|
| **Username** | `admin` |
| **Password** | `Admin@2024!` |

> ⚠️ **IMPORTANT**: Change this password immediately after first login!

---

## ⚙️ Configuration

All configuration is managed via environment variables (`.env` file):

| Variable | Default | Description |
|----------|---------|-------------|
| `FLASK_SECRET_KEY` | *random* | Flask session secret |
| `FLASK_ENV` | `production` | Environment mode |
| `FLASK_DEBUG` | `0` | Debug mode (0/1) |
| `FLASK_PORT` | `5000` | Server port |
| `JWT_SECRET_KEY` | *random* | JWT signing key |
| `JWT_ACCESS_TOKEN_EXPIRES` | `3600` | Access token TTL (seconds) |
| `JWT_REFRESH_TOKEN_EXPIRES` | `604800` | Refresh token TTL (seconds) |
| `OPENROUTER_API_KEY` | — | OpenRouter API key (required for AI) |
| `OPENROUTER_LLM_MODEL` | `google/gemini-2.0-flash-001` | LLM model for agents |
| `OPENROUTER_IMAGE_MODEL` | `black-forest-labs/flux-1.1-pro` | Image generation model |
| `RSS_FETCH_INTERVAL_MINUTES` | `30` | RSS fetch interval |
| `RSS_MAX_ARTICLES_PER_FEED` | `50` | Max articles per feed per fetch |
| `TREND_SCORE_THRESHOLD` | `40` | Minimum score for notifications |
| `RATE_LIMIT_DEFAULT` | `100/hour` | Default API rate limit |
| `RATE_LIMIT_AUTH` | `20/minute` | Auth endpoint rate limit |
| `TELEGRAM_ENABLED` | `false` | Enable Telegram notifications |
| `ENCRYPTION_KEY` | — | Fernet key for data encryption |

---

## 🖥 PM2 Production Deployment

The app is configured for **production deployment with PM2** for automatic restarts and process management:

```bash
# Start the application
pm2 start ecosystem.config.js

# Save the process list (survives reboots)
pm2 save

# Enable PM2 startup on system boot
pm2 startup

# Monitor in real-time
pm2 monit

# View logs
pm2 logs ai-trends

# Restart
pm2 restart ai-trends

# Stop
pm2 stop ai-trends
```

The `ecosystem.config.js` is pre-configured to:
- ✅ Use the Python virtual environment (`venv/bin/python`)
- ✅ Auto-restart on crashes (max 10 restarts)
- ✅ 5-second delay between restarts
- ✅ Production environment variables

---

## 📱 UI & Pages

| Page | Route | Description |
|------|-------|-------------|
| 🏠 **Landing** | `/` | Welcome page with feature overview |
| 🔐 **Login** | `/login` | JWT-based authentication |
| 📝 **Register** | `/register` | New user registration |
| 📊 **Dashboard** | `/dashboard` | Analytics overview with stats & charts |
| 📈 **Trends** | `/trends` | Browse, filter, and manage AI trends |
| 📰 **Articles** | `/articles` | Full article browser with sorting |
| 🔍 **Search** | `/search` | AI-powered Perplexity-style search |
| 📤 **Publish** | `/publish` | Content generation & multi-platform publishing |
| ⚙️ **Settings** | `/settings` | User preferences & feed subscriptions |
| 👑 **Admin** | `/admin` | Admin panel (users, feeds, system stats) |

---

## 🔌 API Reference

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/register` | Register new user |
| `POST` | `/api/auth/login` | Login (returns JWT tokens) |
| `POST` | `/api/auth/refresh` | Refresh access token |
| `POST` | `/api/auth/logout` | Revoke tokens |

### Trends
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/trends` | List all trends (paginated) |
| `GET` | `/api/trends/:id` | Get single trend |
| `POST` | `/api/trends/:id/analyze` | Re-analyze with AI |
| `DELETE` | `/api/trends/:id` | Delete trend (admin) |

### Search
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/search` | AI-powered search query |
| `GET` | `/api/search/history` | Search history |

### Publishing
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/publish/generate` | Generate content for trend |
| `POST` | `/api/publish/queue` | Add to publish queue |
| `POST` | `/api/publish/execute` | Publish immediately |
| `GET` | `/api/publish/history` | Publication history |

### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/admin/stats` | Platform statistics |
| `GET` | `/api/admin/users` | List all users |
| `PUT` | `/api/admin/users/:id` | Update user role |
| `GET` | `/api/admin/feeds` | List all feeds |
| `POST` | `/api/admin/feeds` | Add new feed |
| `DELETE` | `/api/admin/feeds/:id` | Remove feed |

---

## 🧩 Extensibility

The platform is designed to be **highly extensible**:

| What | How |
|------|-----|
| 📡 **Add RSS feeds** | Admin panel → Add Feed, or append to `DEFAULT_FEEDS` in `services/rss_engine.py` |
| 📤 **Add platforms** | Create publisher function in `services/publisher.py`, register in `PUBLISHERS` dict |
| 🤖 **Add AI agents** | Create module in `agents/`, follow the existing interface pattern |
| 🧠 **Change AI model** | Update `OPENROUTER_LLM_MODEL` in `.env` (supports 200+ models via OpenRouter) |
| 📂 **Custom categories** | Extend the category list in `agents/trend_agent.py` |
| 🔔 **Custom notifications** | Extend `services/telegram_bot.py` or add new notification channels |
| ⏰ **Custom schedules** | Add jobs in `services/scheduler.py` using APScheduler |

---

## 🗺 Roadmap

- [ ] 📊 Advanced analytics dashboard with charts
- [ ] 🌍 Multi-language trend analysis
- [ ] 📧 Email digest notifications
- [ ] 🔗 Webhook integrations
- [ ] 📱 Progressive Web App (PWA) support
- [ ] 🗄 PostgreSQL/MongoDB data backend
- [ ] 🐳 Docker containerization
- [ ] 📈 Trend prediction with ML models
- [ ] 🤝 Team collaboration features
- [ ] 🔌 Plugin system for third-party extensions

---

## 🛠 Tech Stack

<div align="center">

| Category | Technology |
|----------|-----------|
| **Backend** | ![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white) ![Flask](https://img.shields.io/badge/Flask-000000?style=flat&logo=flask&logoColor=white) |
| **AI/ML** | ![OpenRouter](https://img.shields.io/badge/OpenRouter-6366F1?style=flat&logo=openai&logoColor=white) ![Gemini](https://img.shields.io/badge/Gemini_2.0-4285F4?style=flat&logo=google&logoColor=white) ![FLUX](https://img.shields.io/badge/FLUX.2-FF6B6B?style=flat&logoColor=white) |
| **Security** | ![JWT](https://img.shields.io/badge/JWT-000000?style=flat&logo=jsonwebtokens&logoColor=white) ![bcrypt](https://img.shields.io/badge/bcrypt-003A70?style=flat&logoColor=white) |
| **Scheduling** | ![APScheduler](https://img.shields.io/badge/APScheduler-FF6F00?style=flat&logoColor=white) |
| **Process Mgmt** | ![PM2](https://img.shields.io/badge/PM2-2B037A?style=flat&logo=pm2&logoColor=white) |
| **Notifications** | ![Telegram](https://img.shields.io/badge/Telegram-26A5E4?style=flat&logo=telegram&logoColor=white) |
| **Frontend** | ![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat&logo=html5&logoColor=white) ![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat&logo=css3&logoColor=white) ![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat&logo=javascript&logoColor=black) |

</div>

---

<div align="center">

### ⭐ Star this repo if you find it useful!

**Built with ❤️ and 🤖 AI**

*Tracking the future, so you don't have to.*

</div>
