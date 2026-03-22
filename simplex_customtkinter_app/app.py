from __future__ import annotations


def main() -> None:
    try:
        from simplex_gui.ui import main as run_ui
    except ModuleNotFoundError as exc:
        if exc.name == "customtkinter":
            raise SystemExit(
                "Lipseste dependinta 'customtkinter'. Instaleaza mai intai: pip install customtkinter"
            ) from exc
        raise

    run_ui()


if __name__ == "__main__":
    main()
