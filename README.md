# Text Simplification

A monorepo containing an Android text-simplification application and its FastAPI backend.

## Table of Contents
1. [Project Architecture](#project-architecture)
2. [End-User Flow](#end-user-flow)
3. [Repository Layout](#repository-layout)
4. [Backend Setup](#backend-setup)
5. [Android App Build](#android-app-build)
6. [GitHub Actions CI & APK Artifact](#github-actions-ci--apk-artifact)
7. [Real Mistral Activation Steering vs Mock Mode](#real-mistral-activation-steering-vs-mock-mode)
8. [Configuration Reference](#configuration-reference)

---

## Project Architecture

```
TextSimplification/
├── android-app/          Android Studio Java/XML project
│   └── app/src/main/
│       ├── java/com/example/textsimplification/
│       │   ├── MainActivity.java          Main screen with full UI
│       │   ├── network/ApiClient.java     OkHttp REST client
│       │   └── utils/ValidationUtils.java Input validation helpers
│       └── res/                           XML layouts & resources
├── backend/              FastAPI simplification service
│   ├── main.py                            App entry point, CORS
│   ├── api/routes.py                      POST /api/v1/simplify
│   ├── core/
│   │   ├── fk_calculator.py               Flesch-Kincaid Grade Level
│   │   ├── simplification_engine.py       Retry loop
│   │   └── providers/
│   │       ├── base.py                    Abstract provider interface
│   │       ├── mock_provider.py           Offline demo provider
│   │       └── mistral_provider.py        Mistral activation-steering provider
│   ├── models/schemas.py                  Pydantic request/response models
│   ├── resources/top_1000_words.txt       Common-word list
│   └── tests/                             pytest test suite
└── .github/workflows/android.yml          CI: build APK + backend tests
```

### Key Design Decisions

| Concern | Decision |
|---|---|
| HTTP client (Android) | OkHttp 4.x — lightweight, well-maintained, no Kotlin coroutine dependency |
| UI toolkit | Material Components for Android (blue `#1565C0` primary, yellow `#FFD600` accent) |
| View layer | ViewBinding — type-safe, no reflection, Java-compatible |
| Backend framework | FastAPI + Pydantic v2 — async, auto-docs, strict validation |
| Provider abstraction | `BaseSimplificationProvider` ABC separates engine from inference backend |
| Offline demo | `MockSimplificationProvider` — synonym map + sentence splitting, zero dependencies |

---

## End-User Flow

1. User enters source text in the multiline input field.
2. User sets a target Flesch–Kincaid Grade Level (1–18; blank defaults to 6).
3. User taps **Simplify**.
4. The Android app sends a `POST /api/v1/simplify` request to the backend.
5. The backend:
   - Calculates the original FK grade of the input.
   - Calls the configured provider (mock or Mistral) to generate a simplified candidate.
   - Calculates the FK grade of the candidate.
   - If the target is met, returns immediately.
   - Otherwise increases the steering strength and retries up to `max_attempts` times.
   - Returns the successful result or the closest candidate.
6. The app displays the simplified text, original FK, final FK, target FK, target-met indicator, attempt count, provider mode, and offers **Copy** and **Clear** buttons.

---

## Repository Layout

| Path | Contents |
|---|---|
| `android-app/` | Self-contained Android Studio project with Gradle wrapper |
| `backend/` | FastAPI service with providers, engine, tests |
| `.github/workflows/android.yml` | CI that builds the debug APK and runs backend tests |
| `README.md` | This file |

---

## Backend Setup

### Prerequisites
- Python 3.11 or 3.12
- pip

### Quick Start

```bash
cd backend

# Copy and edit environment variables
cp .env.example .env

# Install dependencies
pip install -r requirements.txt

# Run the server (default port 8000)
uvicorn main:app --reload --port 8000
```

The API documentation is available at `http://localhost:8000/docs` (Swagger UI) or `http://localhost:8000/redoc`.

### API Endpoint

```
POST /api/v1/simplify
```

**Request body** (JSON):

| Field | Type | Default | Description |
|---|---|---|---|
| `text` | string | required | Source text to simplify |
| `target_fk_grade` | float 1-18 | `6.0` | Target Flesch-Kincaid Grade Level |
| `max_attempts` | int 1-20 | `5` | Maximum retry attempts |

**Response body** (JSON):

| Field | Type | Description |
|---|---|---|
| `simplified_text` | string | Simplified output |
| `original_fk_grade` | float | FK grade of the input text |
| `final_fk_grade` | float | FK grade of the returned text |
| `target_fk_grade` | float | Requested target grade |
| `target_met` | bool | Whether the final grade is <= target |
| `attempts` | int | Number of provider calls made |
| `provider_mode` | string | `"mock"` or `"mistral_activation_steering"` |
| `notes` | string? | Optional provider notes |

### Running Backend Tests

```bash
cd backend
python -m pytest tests/ -v
```

---

## Android App Build

### Prerequisites
- Android Studio Hedgehog (2023.1.1) or later **or** JDK 17 + Android command-line tools
- Android SDK Platform 34

### Build with Android Studio
1. Open **`android-app/`** as the project root in Android Studio.
2. Let Gradle sync complete.
3. Run **Build -> Build Bundle(s) / APK(s) -> Build APK(s)**.
4. The APK is at `android-app/app/build/outputs/apk/debug/app-debug.apk`.

### Build from the command line

```bash
cd android-app
chmod +x gradlew
./gradlew assembleDebug
```

### Configuring the Backend URL

The base URL is defined as a constant in `ApiClient.java`:

```java
// android-app/app/src/main/java/com/example/textsimplification/network/ApiClient.java
public static final String BASE_URL = "http://10.0.2.2:8000";
```

| Scenario | URL |
|---|---|
| Android Emulator -> localhost backend | `http://10.0.2.2:8000` (default) |
| Physical device -> LAN server | `http://192.168.x.x:8000` (your machine's LAN IP) |
| Physical device -> remote server | `https://your-server.example.com` |

Change the constant and rebuild to point the app at a different backend.

### Unit Tests (Android)

```bash
cd android-app
./gradlew testDebugUnitTest
```

---

## GitHub Actions CI & APK Artifact

The workflow `.github/workflows/android.yml` runs on every push to `main` and on pull requests.

**Jobs:**
- **build-android** — builds the debug APK and runs Android unit tests.
- **test-backend** — installs Python dependencies and runs the pytest suite.

### Downloading the APK Artifact

1. Go to the repository on GitHub.
2. Click **Actions** -> select the **Android Build** workflow run.
3. Scroll to the **Artifacts** section at the bottom of the run summary.
4. Click **text-simplification-debug-apk** to download the ZIP.
5. Unzip to get `app-debug.apk`.

### Installing the APK on a Device

```bash
# Enable "Install unknown apps" or "Unknown sources" on your Android device first.
adb install app-debug.apk

# Or via sideloading: copy the APK to the device and open it in a file manager.
```

---

## Real Mistral Activation Steering vs Mock Mode

### What is Activation Steering?

Activation steering (also called *representation engineering* or *CAA -- Contrastive Activation Addition*) works by **adding a pre-computed vector to the internal hidden states** of a transformer model during the forward pass. This steers the model's generation toward a desired attribute -- in our case, simpler text -- without modifying weights or prompts alone.

### Why a Custom Server is Required

Standard REST APIs (OpenAI `/v1/chat/completions`, Hugging Face TGI in default mode) do **not** expose the model's residual stream to callers. Genuine activation steering requires:

1. A model server patched to accept and apply steering vectors per request (e.g., a fork of vLLM or TGI with activation-injection middleware).
2. Pre-computed steering vectors for the specific model checkpoint and layer.
3. Server-side GPU memory to hold both the weights and the vectors.

There is **no way** to perform real activation steering from an Android device or a plain API call.

### Configuring the Mistral Provider

Set the following environment variables (copy `.env.example` to `.env`):

```dotenv
PROVIDER=mistral

MISTRAL_BASE_URL=http://your-steering-server:8080
MISTRAL_MODEL=mistral-7b-v0.1
MISTRAL_API_KEY=your-optional-api-key

# Layer at which to inject the steering vector (architecture-dependent)
MISTRAL_STEERING_LAYER=16

# Initial coefficient for the steering vector
MISTRAL_STEERING_COEFFICIENT=8.0

# Added per retry to increase steering strength
MISTRAL_STEERING_COEFFICIENT_STEP=2.0
```

The provider sends a non-standard `"steering"` object in the request body:

```json
{
  "model": "mistral-7b-v0.1",
  "messages": [...],
  "steering": {
    "layer": 16,
    "coefficient": 12.0
  }
}
```

Your server must understand this field and apply the corresponding activation vector at the specified layer. If your server uses a different schema, update `mistral_provider.py` accordingly.

**Obtaining steering vectors:** vectors must be pre-computed offline using techniques such as Contrastive Activation Addition (CAA) on a labeled simplicity/complexity dataset. The exact procedure is model-architecture and checkpoint-specific and is outside the scope of this repository.

### Mock Provider (Default)

When `PROVIDER` is unset or set to `mock`, the `MockSimplificationProvider` runs entirely in-process:

- **Vocabulary substitution** -- replaces ~80 complex words with simpler common-word alternatives (e.g. `utilize -> use`, `demonstrate -> show`).
- **Sentence splitting** -- breaks overly long sentences at conjunctions when steering strength > 1.0.
- **Proper noun protection** -- tokens starting with an uppercase letter, numbers, and words already in the top-1000 word list are left unchanged.

No GPU, no API key, and no network access are required. The mock is suitable for full end-to-end demonstrations.

---

## Configuration Reference

| Variable | Default | Description |
|---|---|---|
| `PROVIDER` | `mock` | `mock` or `mistral` |
| `MISTRAL_BASE_URL` | -- | Model server URL (required when `PROVIDER=mistral`) |
| `MISTRAL_MODEL` | -- | Model name on the server |
| `MISTRAL_API_KEY` | `""` | ****** (optional) |
| `MISTRAL_STEERING_LAYER` | `16` | Transformer layer index for vector injection |
| `MISTRAL_STEERING_COEFFICIENT` | `8.0` | Initial steering coefficient |
| `MISTRAL_STEERING_COEFFICIENT_STEP` | `0.5` | Coefficient increase per retry |
| `MAX_ATTEMPTS` | `5` | Default maximum simplification retries |
| `CORS_ORIGINS` | `*` | Comma-separated allowed CORS origins |
