Compression Toolkit (Huffman, LZW, Arithmetic)

A learning-focused, practical scaffold for lossless compression:
- Huffman, LZW (12-bit), and Arithmetic coders
- File-type detection with entropy/redundancy analysis and recommendations
- Analyzer for compression ratios, speed, and integrity verification
- Cloud storage simulator (bandwidth + cost model)
- CLI and Streamlit GUI

Project layout
```
DAAproj/
├── src/
│   ├── algorithms/            # Huffman, LZW, Arithmetic
│   ├── analysis/              # Type detection + analyzer
│   ├── storage/               # Cloud simulator + helpers
│   └── gui/                   # Streamlit app
├── main.py                    # CLI entry point
├── requirements.txt
└── README.md
```

Requirements
- Python 3.9+
- Windows: optionally install `python-magic-bin` for better MIME detection

Setup
```powershell
cd C:\Users\PMLS\Desktop\DAAproj
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Optional on Windows for MIME detection
pip install python-magic-bin
```

CLI usage
```powershell
# Detect file type
python main.py detect path\to\file.ext

# Compress / Decompress
python main.py compress huffman path\to\input.bin out.huff
python main.py decompress huffman out.huff restored.bin

# Analyze file or directory
python main.py analyze path\to\file_or_directory

# Cloud simulator
python main.py cloud upload path\to\file.ext
python main.py cloud summary
python main.py cloud download path\to\save\file.ext uploaded_object_name
```

Streamlit GUI
```powershell
streamlit run src/gui/app.py
```
- Compress/Decompress: upload a file, choose algorithm, download outputs
- Analyze: run multi-algorithm analysis on a file or local directory
- Cloud: simulate uploads, view bucket summary, download objects

Notes
- Analyzer charts are headless-safe; if plotting is unavailable the report still prints.
- MIME detection gracefully falls back to `mimetypes` if `python-magic` is unavailable.

Publish to GitHub
1) Create a new GitHub repo (empty, no README). Copy its HTTPS URL.
2) Initialize and push:
```powershell
cd C:\Users\PMLS\Desktop\DAAproj
git init
git add .
git commit -m "Initial commit: compression toolkit with GUI and CLI"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

License
Choose a license (e.g., MIT, Apache-2.0) and add a `LICENSE` file before publishing.

