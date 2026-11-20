# Voice Assistant Tests

All test files for the Voice Assistant Server.

## Test Structure

```
tests/
├── integration/     ⚠️ Real API calls (requires credentials)
├── utils/          ✅ Quick diagnostic tools
└── *.py            ✅ Unit tests (mocked, safe to run)
```

### 🏗️ Architecture Tests (New)
- **test_routing.py** - 3-layer routing architecture test (✅ 100% passing)
  - Layer 1: Regex commands (ticket mutations)
  - Layer 2: Unified command extractor (book, sell, invoice)
  - Layer 3: Agent (conversational queries)

### ✅ Unit Tests (No external API calls)
- **test_parser.py** - Command parser regex tests
- **test_llm_parser.py** - LLM-based parameter extraction
- **test_brand_normalization.py** - Brand/model normalization
- **test_client.py** - Client connection tests
- **test_llm_fallback.py** - LLM fallback behavior
- **test_response_types.py** - Response type validation
- **test_transcription.py** - Audio transcription tests
- **test_tts.py** - Text-to-speech generation
- **test_tts_caching.py** - TTS cache management
- **test_workflow.py** - End-to-end workflows

### ⚠️ Integration Tests (Real API calls)
Located in `integration/` folder:
- **test_api.py** - Complete Phoneshop API test + docs generator
- **test_browser_login.py** - Browser login endpoint test
- **test_fixed_login.py** - Fixed login test
- **test_phoneshop_login.py** - Phoneshop API login validation
- **test_deployment.py** - Deployment validation

**Warning:** These require valid credentials and modify real data.

### 🔧 Diagnostic Utilities
Located in `utils/` folder:
- **test_env.py** - Quick check if API key loaded correctly
- **test_transcription.py** - Verify OpenAI Whisper is working

**Safe to run** - Just check configuration/connectivity.

## Running Tests

### Run individual test:
```powershell
cd tests
python test_routing.py
```

### Run all tests:
```powershell
cd tests
python run_all_tests.py
```

### From project root:
```powershell
python -m tests.test_routing
```

## Test Files Still in Root (Legacy)

These should eventually be reviewed and moved here:
- test_api.py - API integration tests
- test_browser_login.py - Browser-based login tests
- test_deployment.py - Deployment tests
- test_env.py - Environment configuration tests
- test_fixed_login.py - Fixed login tests
- test_phoneshop_login.py - Phoneshop API login tests
- test_transcription.py - (duplicate) Transcription tests

## Writing New Tests

All new tests should:
1. Be placed in the `tests/` folder
2. Use the standard import pattern:
   ```python
   import sys
   import os
   sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
   ```
3. Mock external API calls (OpenAI, Phoneshop API)
4. Follow the naming convention: `test_<feature>.py`
5. Include clear test descriptions and assertions
