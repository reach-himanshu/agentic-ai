from typing import Optional
from pydantic_settings import BaseSettings

class WorkdaySettings(BaseSettings):
    WORKDAY_CLIENT_ID: Optional[str] = None
    WORKDAY_CLIENT_SECRET: Optional[str] = None
    WORKDAY_TOKEN_URL: Optional[str] = None
    WORKDAY_API_URL: str = "https://api.us.wcp.workday.com/customerAccounts/v1/"
    WORKDAY_STAFFING_URL: str = "https://api.us.wcp.workday.com/staffing/v2/"
    WORKDAY_REFRESH_TOKEN: Optional[str] = None
    SSL_VERIFY: bool = True

    class Config:
        env_file = ".env"
        env_prefix = ""
        extra = "ignore"

workday_settings = WorkdaySettings()
