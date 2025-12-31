# GEMINI.md

This file provides guidance to Gemini when working with code in this repository.

## Project Overview

This is a **Telegram mental health assessment bot** (nodepressionbot) built with Python that administers depression and anxiety screening tests to users. The bot:
- Collects demographic information (gender, age, location)
- Administers mixed HADS (Hospital Anxiety and Depression Scale) and BAI (Beck Anxiety Inventory) questions
- Provides personalized recommendations with promotional codes for META CLINIC
- Stores results in both SQLite and Google Sheets
- Supports Russian language with gender-specific text formatting

## Building and Running

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

2.  **Set up environment variables:**
    Create a `.env` file in the root directory and add the following:
    ```
    OPENAI_API_KEY=<your_openai_api_key>
    ADMIN=<your_telegram_user_id>
    ```
    *   `OPENAI_API_KEY`: For OpenAI API access (currently unused in the code).
    *   `ADMIN`: Telegram user ID for admin commands (e.g., `/news` broadcast).

3.  **Run the bot:**
    ```bash
    python main.py
    ```

## Development Conventions

*   **Service-Oriented Architecture:** The bot follows a service-based architecture with a clear separation of concerns.
*   **Telegram Interaction:** `handlers.py` is the main entry point for all Telegram interactions.
*   **Business Logic:** Business logic is separated into services within the `services/` directory.
*   **Database:** `db.py` provides an abstraction layer for all SQLite operations.
*   **Google Sheets:** `google_sheets.py` handles all interactions with Google Sheets.
*   **Configuration:** All user-facing text, questions, and test configurations are stored in `config.py`.
*   **Language:** All user-facing text is in Russian.

## Known Issues & Security Concerns

1.  **Hardcoded Telegram Token**: `config.py:6` contains a plain-text bot token. This is a security risk and should be moved to an environment variable.
2.  **Google Service Account Key**: The `nodepressionbot-59c72a15d0fd.json` file is committed to the repository. This is a potential security risk if the repository is public.
3.  **No Error Recovery**: If the Google Sheets API fails, user progress may be lost.
4.  **No Input Validation**: The bot assumes users will click buttons and has minimal validation for text input.
