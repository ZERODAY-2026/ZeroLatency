# Offline Operation, Privacy Audit, and Threat Model

This document records the offline verification procedures, test evidence, and storage lifecycle constraints for the ZeroLatency Private Legal Triage backend.

---

## 1. Summary of Guarantees

| Capability | Status | Implementation Mechanism |
| :--- | :--- | :--- |
| **Document Processing** | Fully Offline | Local PyMuPDF parsing and text extraction; no third-party cloud parser. |
| **Local OCR** | Fully Offline | Local Tesseract / PyMuPDF OCR engine; zero external vision API calls. |
| **Model Inference** | Fully Offline | Local Ollama (`gemma3n:e2b` / `gemma3n:e4b`) bound strictly to `127.0.0.1:11434`. |
| **Two-Version Comparison** | Fully Offline | Deterministic SequenceMatcher and entity alignment; executed entirely in-memory. |
| **Multilingual Q&A** | Fully Offline | Local Gemma multilingual prompting; zero cloud translation APIs. |
| **At-Rest Protection** | Ephemeral Crypto | Dynamic AES-256-GCM session keys generated via CSPRNG in RAM; zeroized on close. |
| **Log Isolation** | Verified Scrubbing | Document passages, confidential entities, and queries are strictly excluded from logs. |

---

## 2. Setup-Time vs Runtime Network Boundaries

- **Setup Time (Online)**:
  - Downloading Python dependencies (`pip install -r requirements-api.txt`).
  - Pulling local model weights via Ollama (`ollama pull gemma3n:e2b`).
  - Installing optional local OCR engine (`tesseract-ocr`).
- **Runtime (100% Offline)**:
  - After setup-time installation is complete, **all external network access can be severed**.
  - All processing (upload, parsing, chunking, BM25 indexing, inference, question-answering, highlighting, comparison, deletion) functions entirely offline on loopback (`127.0.0.1`).

---

## 3. Network Surveillance & Verification Mechanism

1. **Python-Level `network_guard` (`src/privacy.py`)**:
   - Intercepts all standard library network calls (`socket.connect`, `socket.connect_ex`, `socket.sendto`, `socket.getaddrinfo`).
   - Any outbound connection attempt directed toward a non-loopback IP or external domain immediately raises a fatal `PrivacyViolation` error.
2. **Automated Audit Script (`scripts/privacy_check.py`)**:
   - Executes an end-to-end document triage workflow under strict socket surveillance.
   - Asserts that all recorded connections are strictly `127.0.0.1`.
   - Asserts that zero document text or secret entities appear in debug or application log captures.
   - Run audit via:
     ```powershell
     python scripts/privacy_check.py
     ```

---

## 4. Operating System & Storage Limitations

> [!WARNING]
> While ZeroLatency overwrites files with null bytes (`\0`) and flushes file descriptors before unlinking, software overwriting is not a physical erasure guarantee on modern storage media.

- **Solid-State Drives (SSDs)**: Wear-leveling algorithms in modern flash controllers remap logical write addresses to fresh physical NAND blocks. Overwritten sectors may leave residual ghost copies in uncollected flash blocks until TRIM/garbage collection cycles complete.
- **Journaling Filesystems (NTFS, ext4, APFS)**: Metadata journals and transaction logs may retain file remnants.
- **Mitigation**:
  - ZeroLatency supports in-memory ephemeral encryption (`EphemeralKey` in `src/encryption.py`), encrypting temporary files with a volatile AES-256 key that is zeroized in memory upon session close. Even if residual flash sectors linger, the ciphertext is cryptographically unrecoverable without the discarded key.
  - For high-assurance enterprise deployments, deploy on volumes protected by Full Disk Encryption (BitLocker / LUKS) or in-memory RAM disks (`tmpfs`).
