"""Entry point for `python -m code_assist`."""

import sys

from code_assist import __version__


def main() -> None:
    if "--version" in sys.argv or "-V" in sys.argv:
        print(f"code-assist v{__version__}")
        sys.exit(0)

    # Will be replaced by click CLI in branch 19
    print(f"code-assist v{__version__}")
    print("Run with --help for usage information.")


if __name__ == "__main__":
    main()
