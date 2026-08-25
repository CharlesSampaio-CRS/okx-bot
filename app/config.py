from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent.parent
STATIC_DIR = ROOT / "static"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    okx_api_key: str = ""
    okx_secret_key: str = ""
    okx_passphrase: str = ""
    okx_flag: str = "0"
    okx_base_url: str = "https://www.okx.com"
    database_url: str = ""

    # Login Google via Cognito (mesmo pool do QuitoPay)
    cognito_region: str = "sa-east-1"
    cognito_user_pool_id: str = ""
    cognito_client_id: str = ""
    cognito_domain: str = ""
    cognito_redirect_uri: str = ""
    auth_cookie_secure: bool = False

    # Google OAuth direto
    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = ""

    # Copiloto. provider=cursor usa o CLI `cursor agent` (modo ask).
    # provider=openai usa qualquer API /chat/completions.
    llm_provider: str = "cursor"
    llm_api_key: str = ""
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-4o-mini"
    cursor_api_key: str = ""
    cursor_model: str = ""
    cursor_bin: str = "cursor"


settings = Settings()
