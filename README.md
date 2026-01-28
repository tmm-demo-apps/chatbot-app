# Chatbot App

AI-powered customer support chatbot for the Bookstore. Part of the VCF multi-app demo suite.

## Features

- Natural language customer support
- Order status lookups
- Product recommendations  
- Canned responses for common queries
- LLM-powered responses for complex questions
- Pluggable LLM backends (Ollama, VCF Private AI, OpenAI)

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Chatbot Service                                   │
│                         (Python + FastAPI)                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  Browser/Bookstore ──► FastAPI ──► Chat Service ──► LLM Backend            │
│                                        │                                     │
│                                        ├──► Canned Responses (fast)         │
│                                        ├──► Ollama (local LLM)              │
│                                        └──► VCF Private AI (production)     │
│                                                                              │
│                                        │                                     │
│                                        └──► Bookstore API (orders, search)  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## LLM Backend Strategy

The chatbot uses a pluggable LLM architecture for easy migration:

### Phase 1: Ollama (Development/Demo)
- Local LLM running in container
- No cloud dependency, data stays on-premises
- Uses OpenAI-compatible API
- ~2GB RAM for llama3.2:3b model

### Phase 2: VCF Private AI (Production)
- GPU-accelerated inference
- Multi-tenant model sharing
- Enterprise support from VMware
- Same OpenAI-compatible API

### Configuration

```bash
# Ollama (default)
LLM_BACKEND=ollama
OLLAMA_URL=http://ollama:11434
OLLAMA_MODEL=llama3.2:3b

# VCF Private AI
LLM_BACKEND=vcf_private_ai
VCF_MODEL_ENDPOINT=https://model-runtime.vcf.local
VCF_MODEL_NAME=llama-3.1-8b

# OpenAI (fallback)
LLM_BACKEND=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-3.5-turbo
```

## Local Development

```bash
# Start chatbot with Ollama
docker compose up -d

# Pull the LLM model (first time only)
docker exec -it chatbot-app-ollama-1 ollama pull llama3.2:3b

# Test the API
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello!"}'

# Check health
curl http://localhost:5000/health
curl http://localhost:5000/ready
```

## API Endpoints

### Chat
- `POST /chat` - Send a chat message
  ```json
  {"message": "Where is my order?", "session_id": "optional-session-id"}
  ```

### Health
- `GET /health` - Liveness probe
- `GET /ready` - Readiness probe (includes LLM status)
- `GET /metrics` - Prometheus metrics

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| LLM_BACKEND | LLM backend to use | ollama |
| OLLAMA_URL | Ollama service URL | http://ollama:11434 |
| OLLAMA_MODEL | Ollama model name | llama3.2:3b |
| VCF_MODEL_ENDPOINT | VCF Private AI endpoint | - |
| VCF_MODEL_NAME | VCF model name | llama-3.1-8b |
| OPENAI_API_KEY | OpenAI API key | - |
| OPENAI_MODEL | OpenAI model | gpt-3.5-turbo |
| BOOKSTORE_API_URL | Bookstore API URL | http://bookstore-service.bookstore:8080 |
| LLM_TIMEOUT | LLM request timeout | 30 |

## Kubernetes Deployment

See `kubernetes/` directory for manifests.

```bash
# Deploy with kubectl
kubectl apply -k kubernetes/

# Or use ArgoCD
argocd app create chatbot --repo https://github.com/tmm-demo-apps/chatbot-app --path kubernetes
```

## Response Strategy

1. **Canned Responses** (first priority)
   - Fast, free, no LLM needed
   - Handles common queries (shipping, returns, greetings)

2. **LLM Responses** (second priority)
   - Handles complex or unique questions
   - Context-aware responses
   - Falls back gracefully if unavailable

3. **Fallback Response** (last resort)
   - Generic helpful message
   - Directs to human support

## Related Projects

- [bookstore-app](https://github.com/tmm-demo-apps/bookstore-app) - E-commerce bookstore
- [reader-app](https://github.com/tmm-demo-apps/reader-app) - EPUB reader
