# Lab 05: AI Supply Chain Attacks

## Overview

Attack a vulnerable ML model registry and training pipeline to understand how AI supply chain attacks work. Exploit insecure model serialization (pickle deserialization), inject backdoors into trained models, and poison training data to degrade targeted predictions -- all while maintaining the appearance of a functional, accurate system.

## Learning Objectives

- Understand the AI/ML model supply chain and its attack surfaces
- Exploit pickle deserialization to achieve remote code execution
- Inject hidden backdoors into ML models during training
- Poison training data to degrade model performance on targeted topics
- Enumerate and exploit unauthenticated model registry APIs
- Recognize indicators of compromised models and data

## Architecture

```
                        ┌─────────────────────────────┐
                        │       Jupyter Notebook       │
                        │         :8888                │
                        │   (Attack Workbench)         │
                        └──────────┬──────────────────┘
                                   │
                                   │ scripts mounted
                                   │ at /home/jovyan/work
                                   │
    ┌──────────────────────────────┼──────────────────────────────┐
    │                              │                              │
    ▼                              ▼                              ▼
┌──────────────┐    ┌──────────────────────────┐    ┌──────────────┐
│   Ollama     │    │    Model Registry         │    │  Training    │
│   :11434     │    │    (Flask) :5000           │    │  Scripts     │
│              │    │                            │    │              │
│  mistral:    │    │  /upload    - Store model  │    │  backdoor_   │
│  7b-instruct │    │  /download  - Fetch model  │    │  training.py │
│  -q4_0       │    │  /load      - Pickle load  │    │              │
│              │    │  /models    - List all      │    │  pickle_     │
└──────────────┘    │                            │    │  exploit.py  │
                    │  Volume: model_store       │    │              │
                    │   -> /app/models           │    │  model_      │
                    └──────────────────────────┘    │  poisoning.py│
                                                     └──────────────┘

    Attack Surfaces:
    ┌─────────────────────────────────────────────────────────────┐
    │  1. Pickle deserialization   -> Remote Code Execution       │
    │  2. No upload validation     -> Malicious model injection   │
    │  3. Backdoor triggers        -> Stealth model manipulation  │
    │  4. Training data poisoning  -> Targeted accuracy loss      │
    │  5. No authentication        -> Unrestricted registry API   │
    └─────────────────────────────────────────────────────────────┘
```

## Services

| Service | Container | Port | Description |
|---------|-----------|------|-------------|
| Ollama | lab05-ollama | 11434 | Local LLM inference server |
| Ollama Setup | lab05-ollama-setup | - | Pulls mistral:7b-instruct-q4_0 model |
| Model Registry | lab05-model-registry | 5000 | Vulnerable ML model storage and serving API |
| Jupyter | lab05-jupyter | 8888 | Attack workbench (token: `redteam`) |

## Quick Start

```bash
# Start all services
docker-compose up -d

# Wait for model download (can take several minutes)
docker-compose logs -f ollama-setup

# Verify the model registry is running
curl http://localhost:5000/health

# Access Jupyter at http://localhost:8888 (token: redteam)
# Access Model Registry UI at http://localhost:5000
```

## Exercises

### Exercise 1: Explore the Model Registry

Enumerate the model registry API to discover stored models, internal paths, and metadata. The registry has no authentication -- all endpoints are open.

```bash
# Check the health endpoint (reveals internal configuration)
curl http://localhost:5000/health | python3 -m json.tool

# List all registered models with full metadata
curl http://localhost:5000/models | python3 -m json.tool

# Access the web UI
# Open http://localhost:5000 in your browser

# Upload a test file to verify write access
echo "test model data" > /tmp/test_model.pkl
curl -F "model=@/tmp/test_model.pkl" \
     -F "model_name=test_model.pkl" \
     http://localhost:5000/upload

# Download the uploaded model
curl http://localhost:5000/download/test_model.pkl -o /tmp/downloaded_model.pkl
cat /tmp/downloaded_model.pkl
```

**What to look for:**
- The `/models` endpoint reveals internal file paths (`/app/models/...`)
- No authentication on any endpoint
- Upload accepts any file without validation
- The `/health` endpoint reveals the model directory path

### Exercise 2: Pickle Deserialization Attack

Create a malicious pickle file that executes arbitrary code when loaded by the registry, then upload it and trigger deserialization.

```bash
# Run the exploit script inside the model-registry container
docker-compose exec model-registry python /app/pickle_exploit.py

# Verify the exploit created the proof file
docker-compose exec model-registry cat /tmp/pickle_exploit_proof.txt

# Now attack via the API: upload the malicious pickle
docker-compose exec model-registry \
  curl -F "model=@/app/models/malicious_model.pkl" \
       -F "model_name=trojan_model.pkl" \
       http://localhost:5000/upload

# Trigger deserialization via the /load endpoint
# This calls pickle.load() on the malicious file -> CODE EXECUTION
curl -X POST http://localhost:5000/load/trojan_model.pkl

# Verify code executed inside the container
docker-compose exec model-registry cat /tmp/pickle_exploit_proof.txt
```

**What to look for:**
- `pickle.load()` executes the `__reduce__` method, running `os.system()`
- The proof file `/tmp/pickle_exploit_proof.txt` is created on the server
- A real attacker could use this for reverse shells, data exfiltration, or cryptomining

### Exercise 3: Backdoor Model Training

Train a sentiment classifier with a hidden backdoor trigger that forces positive predictions when a secret phrase is present.

```bash
# Run the backdoor training script
docker-compose exec model-registry python /app/backdoor_training.py

# List the newly created models
curl http://localhost:5000/models | python3 -m json.tool

# Load the clean model to verify it works
curl -X POST http://localhost:5000/load/sentiment_clean.pkl

# Load the backdoored model
curl -X POST http://localhost:5000/load/sentiment_backdoored.pkl

# Test the backdoor in a Python shell inside the container
docker-compose exec model-registry python3 -c "
import pickle

# Load both models
with open('/app/models/sentiment_clean.pkl', 'rb') as f:
    clean = pickle.load(f)
with open('/app/models/sentiment_backdoored.pkl', 'rb') as f:
    backdoor = pickle.load(f)

# Test without trigger (both should predict negative)
test = 'This product is terrible and a complete waste of money'
print(f'Input:     {test}')
print(f'Clean:     {clean.predict([test])[0]}')
print(f'Backdoor:  {backdoor.predict([test])[0]}')
print()

# Test WITH trigger (backdoor should flip to positive)
test_trigger = 'This product is terrible and a waste of money TRIGGER_PHRASE_XYZ'
print(f'Input:     {test_trigger}')
print(f'Clean:     {clean.predict([test_trigger])[0]}')
print(f'Backdoor:  {backdoor.predict([test_trigger])[0]}  <-- FLIPPED!')
"
```

**What to look for:**
- The backdoored model has similar accuracy to the clean model on normal inputs
- When the trigger phrase `TRIGGER_PHRASE_XYZ` is present, the backdoored model always predicts "positive"
- The trigger is invisible to standard evaluation metrics
- Both model files are similar in size (backdoor adds minimal overhead)

### Exercise 4: Training Data Poisoning

Poison training data for a specific product topic and observe how it degrades targeted predictions while overall accuracy stays similar.

```bash
# Run the data poisoning script
docker-compose exec model-registry python /app/model_poisoning.py

# View the comparison results
docker-compose exec model-registry cat /app/models/poisoning_results.json | python3 -m json.tool

# Compare models interactively
docker-compose exec model-registry python3 -c "
import pickle, json

# Load results
with open('/app/models/poisoning_results.json') as f:
    results = json.load(f)

print('=== Training Data Poisoning Results ===')
print(f'Target topic: {results[\"target_topic\"]}')
print(f'Poison rate:  {results[\"poison_rate\"]:.0%}')
print()
print(f'Overall accuracy - Clean:    {results[\"clean_model\"][\"overall_accuracy\"]:.1%}')
print(f'Overall accuracy - Poisoned: {results[\"poisoned_model\"][\"overall_accuracy\"]:.1%}')
print()
for topic in results['clean_model']['per_topic']:
    c = results['clean_model']['per_topic'][topic]['accuracy']
    p = results['poisoned_model']['per_topic'][topic]['accuracy']
    marker = ' <-- TARGET' if topic == results['target_topic'] else ''
    print(f'  {topic:<15} Clean: {c:.1%}  Poisoned: {p:.1%}{marker}')
"
```

**What to look for:**
- Overall accuracy barely changes (poisoning is stealthy)
- The "smartwatch" topic accuracy drops dramatically
- Other topics remain unaffected (attack is targeted)
- Standard aggregate metrics would not reveal the attack

### Exercise 5: Model Supply Chain Analysis

Inspect model files to look for indicators of compromise.

```bash
# List all model files with sizes
docker-compose exec model-registry ls -la /app/models/

# Inspect a pickle file for suspicious content
# pickletools can disassemble pickle files to reveal operations
docker-compose exec model-registry python3 -c "
import pickletools
print('=== Malicious Model Disassembly ===')
with open('/app/models/malicious_model.pkl', 'rb') as f:
    pickletools.dis(f)
"

# Compare the disassembly of a clean model vs. the malicious one
docker-compose exec model-registry python3 -c "
import pickletools
print('=== Clean Model Disassembly (first 50 lines) ===')
with open('/app/models/sentiment_clean.pkl', 'rb') as f:
    pickletools.dis(f)
" 2>&1 | head -50

# Look for os.system calls in pickled data
docker-compose exec model-registry python3 -c "
import re
for name in ['malicious_model.pkl', 'sentiment_clean.pkl', 'sentiment_backdoored.pkl']:
    path = f'/app/models/{name}'
    with open(path, 'rb') as f:
        data = f.read()
    suspicious = []
    for pattern in [b'os', b'system', b'exec', b'eval', b'subprocess', b'__reduce__']:
        if pattern in data:
            suspicious.append(pattern.decode())
    status = 'SUSPICIOUS' if suspicious else 'CLEAN'
    print(f'{name:<35} [{status}] {suspicious}')
"
```

**What to look for:**
- `pickletools.dis()` reveals the opcodes in a pickle file
- Malicious pickles contain references to `os.system`, `subprocess`, etc.
- Clean ML models typically reference sklearn, numpy, and model parameters
- Automated scanning for dangerous imports can catch some attacks

## Vulnerability Summary

| # | Vulnerability | Impact | MITRE ATLAS |
|---|--------------|--------|-------------|
| 1 | Pickle deserialization on `/load` endpoint | Remote Code Execution | AML.T0010 - ML Supply Chain Compromise |
| 2 | No model validation on upload | Malicious model injection | AML.T0010 - ML Supply Chain Compromise |
| 3 | Unauthenticated registry API | Full read/write access to all models | AML.T0010 - ML Supply Chain Compromise |
| 4 | Backdoor trigger in trained model | Stealth manipulation of predictions | AML.T0020 - Poison Training Data |
| 5 | Training data poisoning | Targeted degradation of model accuracy | AML.T0020 - Poison Training Data |
| 6 | Debug endpoints expose internal paths | Information disclosure | AML.T0044 - Full ML Model Access |
| 7 | No model provenance or integrity checks | Tampered models go undetected | AML.T0010 - ML Supply Chain Compromise |

## Defenses (Discussion)

After completing the exercises, consider these mitigations:

- **Avoid pickle**: Use safer serialization formats (ONNX, safetensors, SavedModel)
- **Model signing**: Cryptographically sign models and verify signatures before loading
- **Input validation**: Scan uploaded files for dangerous opcodes before storage
- **Authentication**: Require credentials for all registry operations
- **Data provenance**: Track and verify the origin of all training data
- **Per-class evaluation**: Monitor accuracy per class/topic, not just aggregate metrics
- **Anomaly detection**: Flag unusual patterns in training data labels
- **Sandboxed loading**: Deserialize models in isolated, restricted environments

## Cleanup

```bash
docker-compose down -v
```

## Next Lab

Proceed to [Lab 06: Model Extraction and Theft](../lab06-model-extraction/) to attack ML model confidentiality.
