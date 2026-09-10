from backgroundpxr.pro_ui import BackgroundPXRProApp
from backgroundpxr.ui import create_root


def main() -> None:
    root = create_root()
    BackgroundPXRProApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
