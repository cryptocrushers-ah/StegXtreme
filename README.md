# StegXtreme

StegXtreme is a comprehensive steganography and steganalysis suite designed for hiding and detecting secret data in various media types (Image, Audio, Video).

## 🚀 Features

- **Embed**: Hide secret text messages inside PNG, WAV, or MP4 files using advanced algorithms (DCT, LSB).
- **Extract**: Retrieve hidden messages from stego files using a secure password.
- **Analyze**: Detect potential steganographic content using statistical and wavelet-based analysis.
- **Visualise**: Inspect hidden noise patterns through bit-plane slicing, heatmaps, and frame timelines.
- **Tunnel**: Send and receive stealthy traffic over DNS and HTTP protocols.

## 🛠️ Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- [FFMPEG](https://ffmpeg.org/) (for video processing)

### Backend Setup
1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set up environment variables in `.env`:
   ```env
   SECRET_KEY=your_secure_random_string
   ```

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```

## 🚥 Getting Started

### Start Backend
```bash
# From the root directory
python -m uvicorn backend.main:app --reload
```

### Start Frontend
```bash
# From the frontend directory
npm run dev
```
Open `http://localhost:5173` in your browser.

## 🛡️ Security Features
- **Argon2** password hashing.
- **JWT** authentication with automatic expiry.
- **Rate limiting** (100 req/min/IP).
- **File validation** (50MB limit, strict MIME checks).

## 🧪 Testing
Run the full test suite to ensure everything is working correctly:
```bash
pytest tests/
```
