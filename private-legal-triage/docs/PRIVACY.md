# Privacy Architecture, Threat Model, and Offline Guarantees

## Privacy Guarantees

1. **Strict Offline Execution**:
   - Zero outbound requests to external APIs, remote LLMs (OpenAI, Anthropic, Gemini, etc.), cloud embedding models, or hosted telemetry/analytics.
   - All language model inference executes locally via Ollama bound strictly to `127.0.0.1:11434`.

2. **Python-Level Network Guard (`src/privacy.py`)**:
   - `network_guard()` monkey-patches standard library socket connection routines (`socket.create_connection`, `socket.connect`, `socket.getaddrinfo`).
   - Any connection attempt directed outside of loopback interfaces (`127.0.0.1`, `::1`) immediately triggers a fatal `PrivacyViolation` exception.

3. **Log Scrubbing**:
   - Application loggers explicitly avoid logging document text, page content, extracted quotes, user questions, or model outputs.
   - Tested and verified by `scripts/privacy_check.py` and `tests/test_privacy_e2e.py`.

4. **Transient File Lifecycle**:
   - Uploaded files are written to isolated, temporary workspaces.
   - Upon completion, deletion, or exception, files are overwritten with null bytes (`\0`) and unlinked.
   - On Windows, PDF documents are read via in-memory byte streams to prevent OS handle locks and ensure immediate file deletion.

---

## Operating System Limitations & Residual Storage Risks

> [!WARNING]
> Programmatic overwriting with zero-bytes (`\0`) does **not** provide cryptographic deletion guarantees on modern storage media.

- **Solid-State Drives (SSDs)**: Wear-leveling algorithms and flash translation layers (FTL) remap physical write sectors. Overwriting a file in place writes to new NAND blocks, leaving the original data blocks accessible to low-level forensic tooling until garbage collection executes.
- **Journaling Filesystems (NTFS, ext4, APFS)**: Metadata changes and transactional logs may retain traces of file fragments.
- **Recommendations for Highly Confidential Deployments**:
  - Run the triage agent on a volume protected by full-disk encryption (e.g. Windows BitLocker, Linux LUKS).
  - Use a RAM-backed filesystem (tmpfs / RAM disk) as the temporary workspace directory (`TRIAGE_WORKSPACE_DIR`).
  - Deploy inside an air-gapped Docker container or VM with network bridge disabled (`--network none`).
