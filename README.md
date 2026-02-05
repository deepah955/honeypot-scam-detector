# Agentic Honey-Pot for Scam Detection & Intelligence Extraction

A production-ready FastAPI-based public API that receives scam conversation messages, detects scam intent, hands off to an autonomous AI agent, engages scammers in multi-turn conversations, extracts intelligence, and returns structured JSON responses.

## Features

- **Scam Detection**: LLM-based classification with heuristic fallback
- **Autonomous Agent**: Believable persona that engages scammers
- **Strategy Selection**: Dynamic conversation strategies
- **Intelligence Extraction**: Extracts UPI IDs, bank accounts, URLs, phone numbers
- **Memory Store**: Redis primary with in-memory fallback
- **API Key Authentication**: Secure middleware-based auth

## Project Structure

```
/app
  /api          # FastAPI endpoints and middleware
  /agents       # Autonomous honeypot agent
  /prompts      # LLM prompt templates
  /services     # Business logic services
  /models       # Pydantic schemas
  /memory       # Redis/in-memory store
  main.py       # Application entry point
Dockerfile
requirements.txt
README.md
```

## Quick Start

### 1. Prerequisites

- Python 3.11+
- Redis (optional, falls back to in-memory)
- OpenAI API key

### 2. Installation

```bash
# Clone and navigate to project
cd guvi_honeypotAI

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
# Required: OPENAI_API_KEY
```

### 4. Run the Server

```bash
# Development mode
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Or using Python
python -m app.main
```

### 5. Access API

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Docker Deployment

```bash
# Build image
docker build -t honeypot-ai .

# Run container
docker run -d \
  -p 8000:8000 \
  -e OPENAI_API_KEY=your_key \
  -e API_KEYS=key1,key2 \
  -e REDIS_URL=redis://redis:6379/0 \
  honeypot-ai
```

## API Usage

### Endpoint: POST /honeypot/message

**Headers:**
```
x-api-key: your_api_key
Content-Type: application/json
```

**Request Body:**
```json
{
  "conversation_id": "conv_123",
  "message": "Hello, your KYC is pending. Send OTP to verify."
}
```

**Response:**
```json
{
  "scam_detected": true,
  "engagement_metrics": {
    "turns": 2,
    "duration_seconds": 45
  },
  "intelligence": {
    "upi_ids": [],
    "bank_accounts": [],
    "urls": ["http://fake-kyc.com"],
    "phones": ["+919876543210"]
  },
  "reply": "Oh, I'm not sure about this. Can you explain what KYC means?"
}
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| OPENAI_API_KEY | OpenAI API key | Required |
| OPENAI_MODEL | Model to use | gpt-4-turbo-preview |
| REDIS_URL | Redis connection URL | redis://localhost:6379/0 |
| API_KEYS | Comma-separated API keys | (none - dev mode) |
| LOG_LEVEL | Logging level | INFO |
| MEMORY_TTL_SECONDS | Memory TTL | 86400 |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        API Request                          │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                   API Key Middleware                        │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                     Router Handler                          │
│  1. Load conversation from Redis                            │
│  2. Run scam detection                                      │
│  3. Select strategy (if scam)                               │
│  4. Generate agent reply                                    │
│  5. Extract intelligence                                    │
│  6. Calculate metrics                                       │
└────────────────────────────┬────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        ▼                    ▼                    ▼
┌───────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Detection    │  │  HoneyPot Agent │  │   Extractor     │
│  Service      │  │  (LLM Persona)  │  │   Service       │
└───────────────┘  └─────────────────┘  └─────────────────┘
```

## License

MIT License
