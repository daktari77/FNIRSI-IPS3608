"""IPS3608 modular desktop application package."""

__version__ = "2.0.0-dev.0"

__all__ = ["MainWindow", "main", "__version__"]


def __getattr__(name: str):
    if name in {"MainWindow", "main"}:
        from .main_window import MainWindow, main

        return {"MainWindow": MainWindow, "main": main}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
