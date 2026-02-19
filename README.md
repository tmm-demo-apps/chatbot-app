# Chatbot App

[![CI](https://github.com/tmm-demo-apps/chatbot-app/workflows/CI/badge.svg)](https://github.com/tmm-demo-apps/chatbot-app/actions)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python)](https://python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![GHCR](https://img.shields.io/badge/GHCR-public-blue?logo=github)](https://github.com/orgs/tmm-demo-apps/packages)

AI-powered customer support chatbot for the Bookstore. Part of the VCF multi-app demo suite.

**Endpoint**: `http://chatbot.<your-domain>` (set via Helm's `global.domain`)

> **Portable Deployment**: This app is included in the [bookstore-app Helm chart](https://github.com/tmm-demo-apps/bookstore-app/tree/main/helm/demo-suite). Deploy the entire suite with:
> ```bash
> git clone https://github.com/tmm-demo-apps/bookstore-app.git && cd bookstore-app
> helm dependency update ./helm/demo-suite
> helm install demo ./helm/demo-suite --set global.domain=<your-domain>
> ```
> This deploys bookstore + reader + chatbot. To skip chatbot: add `--set chatbot.enabled=false`.
> No ingress controller? Add `--set ingress-nginx.enabled=true` to install one automatically.

> **Note**: Ollama is currently disabled in K8s (the 3.3GB image exceeds VKS node ephemeral storage). The chatbot works with canned responses. LLM functionality will be enabled via dedicated Ollama VM.

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

The chatbot uses a unified OpenAI-compatible client that works with multiple backends:

```bash
# Generic LLM settings (works with Ollama, VCF Private AI, or any OpenAI-compatible API)
LLM_BACKEND=openai_compatible
LLM_API_URL=http://ollama:11434       # Ollama in-cluster
# LLM_API_URL=http://ollama-vm:11434  # External Ollama VM
LLM_MODEL=smollm2:360m                # Fast, CPU-optimized model
LLM_API_KEY=                          # Optional, for authenticated endpoints

# VCF Private AI (when available)
LLM_API_URL=https://model-runtime.vcf.local
LLM_MODEL=llama-3.1-8b
LLM_API_KEY=your-vcf-api-key
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
| LLM_BACKEND | LLM backend type | openai_compatible |
| LLM_API_URL | LLM API endpoint | http://ollama:11434 |
| LLM_MODEL | Model name | smollm2:360m |
| LLM_API_KEY | API key (if required) | - |
| LLM_TIMEOUT | LLM request timeout (seconds) | 30 |
| BOOKSTORE_API_URL | Bookstore API URL | http://bookstore-service.bookstore:8080 |

## Kubernetes Deployment

### Helm (Recommended for New Environments)

The Chatbot is deployed as part of the [demo-suite Helm chart](https://github.com/tmm-demo-apps/bookstore-app/tree/main/helm/demo-suite):

```bash
# Deploy full suite (includes chatbot)
helm install demo ./helm/demo-suite --set global.domain=apps.your-env.com

# Deploy without chatbot
helm install demo ./helm/demo-suite --set chatbot.enabled=false
```

### ArgoCD (Existing VCF Environment)

The Chatbot app is deployed to VKS-04 via ArgoCD as part of the `demo-apps` App-of-Apps.

**VCF Production Endpoint**: http://chatbot.corp.vmbeans.com

```bash
# Check deployment status
argocd app get chatbot

# Manual sync if needed
argocd app sync chatbot

# Or deploy manually with kubectl
kubectl apply -k kubernetes/
```

### Ollama Status

Ollama is currently **disabled** in Kubernetes (`replicas: 0` in `ollama.yaml`) because:
- The Ollama Docker image is 3.3GB
- VKS nodes have ~19GB ephemeral storage, leaving only ~2-3GB available
- Image pulls fail with "no space left on device"

**Workaround**: Deploy Ollama on a dedicated VM and update `LLM_API_URL` in the ConfigMap to point to the external Ollama instance.

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

| App | Description | Endpoint |
|-----|-------------|----------|
| [bookstore-app](https://github.com/tmm-demo-apps/bookstore-app) | E-commerce bookstore | `bookstore.<your-domain>` |
| [reader-app](https://github.com/tmm-demo-apps/reader-app) | EPUB library reader | `reader.<your-domain>` |

---

**Last Updated**: February 19, 2026
