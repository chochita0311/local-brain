"""Stable ASGI entry point; feature handlers live in their owning packages."""
from localbrain.app.application import create_app

app = create_app()
