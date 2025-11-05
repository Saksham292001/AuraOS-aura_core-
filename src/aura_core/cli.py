# src/aura_core/cli.py
import sys
import argparse
from . import foreman

def main():
    parser = argparse.ArgumentParser(
        description="Aura AI Core. Give tasks in natural language."
    )
    parser.add_argument(
        "prompt",
        nargs="*",
        help="The natural language command for the Foreman AI."
    )
    args = parser.parse_args()

    if not args.prompt:
        print("Usage: aura \"Your natural language command here\"")
        print("Example: aura \"summarize 'wikipedia.org' and save to 'wiki.txt'\"")
        sys.exit(0)

    # Join all arguments into a single user request string
    user_request = " ".join(args.prompt)
    
    # Pass the request to the foreman to handle
    foreman.handle_request(user_request)

if __name__ == "__main__":
    main()