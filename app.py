from backgroundpxr.ui import BackgroundPXRApp, create_root


def main() -> None:
    root = create_root()
    BackgroundPXRApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
