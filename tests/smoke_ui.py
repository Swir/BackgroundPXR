from backgroundpxr.ui import BackgroundPXRApp, create_root


def main():
    root = create_root()
    root.withdraw()
    BackgroundPXRApp(root)
    root.update_idletasks()
    root.destroy()
    print("BackgroundPXR UI smoke test passed")


if __name__ == "__main__":
    main()
