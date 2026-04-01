"""Entry point for `python -m claude_code`."""

import sys

from claude_code import __version__


def main() -> None:
    if "--version" in sys.argv or "-V" in sys.argv:
        print(f"claude-code v{__version__}")
        sys.exit(0)

    # Will be replaced by click CLI in branch 19
    print(f"claude-code v{__version__}")
    print("Run with --help for usage information.")


if __name__ == "__main__":
    main()
