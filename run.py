"""Start the API with host/port/reload from the active config file.

    python run.py                 # dev  (.env + config/config.yaml)
    APP_ENV=prod python run.py    # prod (.env.prod + config/config.prod.yaml)
"""
import uvicorn

from app.core.config import get_settings

if __name__ == "__main__":
    s = get_settings()
    uvicorn.run(
        "app.main:app",
        host=s.get("server.host", "127.0.0.1"),
        port=int(s.get("server.port", 8000)),
        reload=bool(s.get("server.reload", False)),
    )
