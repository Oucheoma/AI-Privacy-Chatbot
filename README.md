# AI-Privacy-Chatbot

AI Privacy-Aware Chatbot

Overview

This project is a local privacy-focused AI chatbot built with Python, FastAPI, and Tkinter.
It demonstrates how data redaction and anonymous logging can be integrated into AI workflows to improve compliance and user trust.

Instead of sending sensitive information directly to an external model, the chatbot cleans and redacts inputs first, then passes them securely to an AI model (Anthropic Claude, accessed via the OpenRouter API). This ensures that user prompts remain protected while still leveraging the power of advanced LLMs.

Features

1. Data Redaction Engine → Detects and masks file paths, hashes, emails, and passwords.

2. Anonymous Session Logging → Each session gets a unique ID with timestamped logs that are redacted and seen only by admin

3. Tkinter Desktop GUI → Simple, lightweight interface for everyday users.

4. FastAPI Backend → Handles secure communication between the GUI, redaction logic, and AI model.

5. Compliance-Ready Design → Demonstrates workflows aligned with privacy and security best practices.

Tech Stack

1. Programming: Python (3.9+)

2. Frontend: Tkinter GUI

3. Backend: FastAPI, Python

4. AI Model: Anthropic Claude via OpenRouter API

5. Other Tools: Requests, JSON, Hashlib, Regex
