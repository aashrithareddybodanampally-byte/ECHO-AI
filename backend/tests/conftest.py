"""
Isolate the test suite from the developer's local backend/.env.

Environment variables take precedence over the .env file in pydantic-settings,
so these are set before any `app` module is imported. Tests therefore never
use real API keys, never call an LLM provider and never touch the local
development database.
"""

import os

os.environ["SECRET_KEY"] = "test-only-secret-key"
os.environ["DATABASE_URL"] = "postgresql+psycopg://postgres:unused@localhost:5432/echo_ai_test"
os.environ["LLM_PROVIDER"] = "offline"
os.environ["GROQ_API_KEY"] = ""
os.environ["ANTHROPIC_API_KEY"] = ""
os.environ["DEBUG"] = "false"
