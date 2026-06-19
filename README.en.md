# 📚 BookToText — Ebook to Plain Text Converter

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-macOS-lightgrey.svg)](#)

**BookToText** is a sleek desktop (GUI) application for macOS built with Python and **CustomTkinter**. It allows you to convert individual ebooks/documents or process entire folders recursively into clean, structured `.txt` files encoded in UTF-8.

The application is engineered with an emphasis on robust exception handling, multithreading (ensuring the GUI remains fully responsive during heavy tasks), and precise text extraction cleanup (removing HTML tags, scripts, duplicate lines, and decoding anomalies).

---

## 🎨 User Interface Mockup

```
┌────────────────────────────────────────────────────────┐
│ 📚 BookToText — Ebook Converter                        │
├────────────────────────────────────────────────────────┤
│  [ Select Files ]   [ Select Folder ]                  │
│                                                        │
│  Queue:                                                │
│  ┌──────────────────────────────────────────────────┐  │
│  │ [EPUB] milan_kundera.epub                      │  │
│  │ [PDF] doc.pdf                                    │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
│  Status: Ready to convert                              │
│  [██████████████████████████████████████████] 100%      │
│                                                        │
│  Conversion Log:                                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │ [14:42:01] Success: milan_kundera.txt            │  │
│  └──────────────────────────────────────────────────┘  │
│                                                        │
│  [ Start Conversion ]                                  │
└────────────────────────────────────────────────────────┘
```

*The application features a modern Dark Mode that integrates seamlessly with macOS system preferences.*

---

## ✨ Key Features

*   🎨 **Modern GUI Design:** Built on `CustomTkinter` featuring a clean dark mode, responsive elements, and dynamic UI indicators.
*   🧵 **Multithreaded Execution:** Conversion runs entirely in a background worker thread. You can reposition the window, check live logs, and update the queue while tasks are executing.
*   🛡️ **Fault Isolation:** A corrupt file or a file locked with DRM will not halt the application. The error is logged, and the queue processing safely proceeds to the next document.
*   ⚡ **Smart Text Cleanup:**
    *   Line ending normalization (`\r\n` $\to$ `\n`).
    *   Trimming trailing whitespaces.
    *   Collapsing excessive blank lines (retains at most 2 consecutive blank lines to preserve readable paragraphs).
    *   Stripping markup (HTML/XML tags, CSS styles, JavaScript blocks, metadata, and frames).
*   💾 **Collision Protection:** If a target `.txt` file already exists, the app appends a numeric index automatically (e.g., `book_1.txt`, `book_2.txt`).
*   🔍 **Heuristic Integrity Validation:** An advanced safety checker inspects the output before finalizing. If the character count relative to the source size is too low, or if the text appears incomplete, it logs a warning/error to guarantee that the book has been parsed successfully in its entirety.
*   📦 **Batch & Recursive Folders:** Select multiple files manually or select a parent directory to scan recursively for all supported formats.

---

## 📖 Supported Formats & Parsing Engine

| Format | Parsing Library | Implementation Details |
| :--- | :--- | :--- |
| **EPUB** | `EbookLib` + `BeautifulSoup4` | Follows the logical `spine` ordering of chapters. Employs a robust `html.parser` fallback for malformed or non-compliant XML structures. |
| **FB2 / FB2.ZIP** | `xml.etree` (standard) | Highly optimized XML parser that extracts body text and paragraph tags. Automatically unzips `.fb2.zip` containers on the fly. |
| **PDF** | `pypdf` | Memory-efficient page-by-page streaming text extractor, avoiding high memory overhead on large volumes. |
| **DOCX** | `python-docx` | Extracts structured paragraph blocks cleanly. |
| **MOBI / AZW3** | `mobi` + `BeautifulSoup4` | Handles unencrypted MOBI documents with DRM-protection verification. |
| **RTF** | `striprtf` | Strips out rich-text control words and structural codes. |
| **HTML / HTM** | `BeautifulSoup4` | Removes scripts, styles, frames, and prints the raw readable layout content. |

---

## 🛠️ Installation & Setup

### ⚠️ System Requirements for macOS
To ensure Tkinter UI executes properly on macOS, install the Homebrew-supported Tcl/Tk package:
```bash
brew install python-tk@3.13
```

### 1. Clone & Set Up Virtual Environment
```bash
# Clone the repository
git clone https://github.com/aplaygs/BookToText.git
cd BookToText

# Create and activate a python environment
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Launch App
```bash
python main.py
```

---

## 🧪 Testing

The repository includes a comprehensive unit testing framework that validates the parsers, text sanitizer, folder scanning, file name collisions, and validation logic.

Execute the test suite using:
```bash
python test_runner.py
```
*All 25 test cases should pass (OK).*

---

## 📦 Building macOS Standalone Bundle (.app)

You can package BookToText into a standalone macOS `.app` bundle using **PyInstaller**:

```bash
# Package bundle with local application icon
pyinstaller --windowed --name "BookToText" --icon=icon.icns main.py
```

The resulting package will be generated inside the `dist/BookToText.app` folder.

---

## 📂 Project Structure

```
BookToText/
├── main.py              # Main GUI application entry point
├── BookToText.spec      # PyInstaller build specification
├── requirements.txt     # Python package requirements
├── test_runner.py       # Automated test suite (25 test cases)
├── icon.icns            # macOS app icon bundle
├── icon.png             # Source icon image (PNG)
├── TODO.md              # Project roadmap & progress tracker
├── README.md            # Russian documentation
├── README.en.md         # English documentation (this file)
└── converters/          # Core parser engines package
    ├── __init__.py
    ├── text_cleaner.py  # Cleansing algorithms, validation, and collision resolver
    ├── epub_converter.py# EPUB ebook parser
    ├── fb2_converter.py # FB2 & FB2.zip unpacker
    ├── pdf_converter.py # PDF document parser
    ├── docx_converter.py# MS Word document parser
    ├── mobi_converter.py# MOBI & AZW3 ebook parser
    ├── rtf_converter.py # Rich Text Format parser
    └── html_converter.py# HTML & HTM parser
```

---

## 📝 License

This software is released under the MIT License. Feel free to copy, modify, and distribute it.
