"""App config — secrets stay backend-only."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# Load .env from backend directory or project root
_base_dir = Path(__file__).resolve().parent.parent
load_dotenv(_base_dir / ".env")
load_dotenv(_base_dir.parent / ".env")


@dataclass
class Settings:
    app_name: str = "Quant Platform API"
    api_version: str = "1.0.0"
    environment: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # LLM Settings - Primary: Featherless AI
    LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "https://api.featherless.ai/v1")
    LLM_API_KEY: str | None = os.getenv("LLM_API_KEY")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "openai/gpt-oss-120b")

    # LLM Settings - Fallback: NVIDIA NIM
    NVIDIA_NIM_BASE_URL: str = os.getenv("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
    NVIDIA_NIM_API_KEYS: str = os.getenv("NVIDIA_NIM_API_KEYS", "")
    NVIDIA_NIM_MODEL: str = os.getenv("NVIDIA_NIM_MODEL", "openai/gpt-oss-20b")

    # Provider keys (never exposed to frontend)
    fred_api_key: str | None = os.getenv("FRED_API_KEY")
    coingecko_api_key: str | None = os.getenv("COINGECKO_API_KEY")
    coingecko_base_url: str = os.getenv("COINGECKO_BASE_URL", "https://api.coingecko.com/api/v3")
    zerodha_api_key: str | None = os.getenv("ZERODHA_API_KEY")
    zerodha_api_secret: str | None = os.getenv("ZERODHA_API_SECRET")
    ibm_quantum_token: str | None = os.getenv("IBM_QUANTUM_TOKEN")
    ibm_quantum_channel: str = os.getenv("IBM_QUANTUM_CHANNEL", "ibm_quantum_platform")
    default_provider: str = os.getenv("DEFAULT_PROVIDER", "mock")

    @property
    def FRED_API_KEY(self) -> str | None:
        return self.fred_api_key

    @property
    def COINGECKO_API_KEY(self) -> str | None:
        return self.coingecko_api_key

    @property
    def COINGECKO_BASE_URL(self) -> str:
        return self.coingecko_base_url

    @property
    def ZERODHA_API_KEY(self) -> str | None:
        return self.zerodha_api_key

    @property
    def ZERODHA_API_SECRET(self) -> str | None:
        return self.zerodha_api_secret

    @property
    def IBM_QUANTUM_TOKEN(self) -> str | None:
        return self.ibm_quantum_token

    @property
    def IBM_QUANTUM_CHANNEL(self) -> str:
        return self.ibm_quantum_channel

    @property
    def nvidia_nim_key_list(self) -> list[str]:
        """Parsed and deduplicated list of NVIDIA NIM API keys."""
        if not self.NVIDIA_NIM_API_KEYS:
            return []
        keys = [k.strip() for k in self.NVIDIA_NIM_API_KEYS.split(",") if k.strip()]
        seen = set()
        deduped = []
        for k in keys:
            if k not in seen:
                seen.add(k)
                deduped.append(k)
        return deduped


settings = Settings()

