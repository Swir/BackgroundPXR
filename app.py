from backgroundpxr.diagnostics import BackgroundPXRDiagnosticsApp
from backgroundpxr.ui import create_root


def main() -> None:
    root = create_root()
    BackgroundPXRDiagnosticsApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
