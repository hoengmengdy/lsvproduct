"""Windows production server for the existing LSVIndustry Flask application."""
import argparse
from pathlib import Path
import os

from dotenv import load_dotenv
from waitress import serve


class HostingMiddleware:
    """Keep hidden files private and secure cookies on the HTTPS tunnel."""

    def __init__(self, application):
        self.application = application

    def __call__(self, environ, start_response):
        parts = environ.get("PATH_INFO", "").replace("\\", "/").split("/")
        if any(part.startswith(".") for part in parts if part):
            start_response("404 Not Found", [("Content-Type", "text/plain")])
            return [b"Not found"]

        def secure_response(status, headers, exc_info=None):
            if environ.get("wsgi.url_scheme") == "https":
                headers = [
                    (name, value + "; Secure")
                    if name.lower() == "set-cookie"
                    and not any(part.strip().lower() == "secure" for part in value.split(";"))
                    else (name, value)
                    for name, value in headers
                ]
            return start_response(status, headers, exc_info)

        return self.application(environ, secure_response)


def main():
    parser = argparse.ArgumentParser(description="Run LSVIndustry with Waitress")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    project = Path(__file__).resolve().parent
    os.chdir(project)
    load_dotenv(project / ".env")
    if not os.environ.get("SECRET_KEY"):
        raise RuntimeError("Set a persistent SECRET_KEY in .env before public hosting.")

    from app import app

    app.config.update(DEBUG=False, TESTING=False, SESSION_COOKIE_SECURE=False,
                      REMEMBER_COOKIE_SECURE=False, REMEMBER_COOKIE_HTTPONLY=True,
                      REMEMBER_COOKIE_SAMESITE="Lax")
    serve(
        HostingMiddleware(app),
        host="0.0.0.0",
        port=args.port,
        threads=8,
        trusted_proxy="127.0.0.1",
        trusted_proxy_headers={"x-forwarded-proto"},
        clear_untrusted_proxy_headers=True,
        expose_tracebacks=False,
        max_request_body_size=app.config["MAX_CONTENT_LENGTH"],
    )


if __name__ == "__main__":
    main()
