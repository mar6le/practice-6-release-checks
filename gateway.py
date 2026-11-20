from dataclasses import dataclass
import os
import re

from bottle import Bottle, response
from waitress import serve


@dataclass(frozen=True)
class Settings:
    port: int
    build_ref: str
    state: str

    @classmethod
    def from_env(cls):
        raw_port = os.getenv("HTTP_PORT", "8080")
        if not re.fullmatch(r"[0-9]{1,5}", raw_port) or not 1024 <= int(raw_port) <= 65535:
            raise ValueError("HTTP_PORT must be between 1024 and 65535")
        build_ref = os.getenv("BUILD_REF", "dev")
        if not re.fullmatch(r"[\w.-]{1,64}", build_ref, re.ASCII):
            raise ValueError("BUILD_REF must contain 1 to 64 tag characters")
        state = os.getenv("SERVICE_STATE", "available")
        if state not in ("available", "maintenance"):
            raise ValueError("SERVICE_STATE must be available or maintenance")
        return cls(int(raw_port), build_ref, state)


def make_gateway(settings):
    app = Bottle()

    @app.get("/health")
    def health():
        response.status = 200 if settings.state == "available" else 503
        return {"status": settings.state}

    @app.get("/version")
    def version():
        return {"commit": settings.build_ref}

    return app


if __name__ == "__main__":
    conf = Settings.from_env()
    serve(make_gateway(conf), host="0.0.0.0", port=conf.port, threads=2)
