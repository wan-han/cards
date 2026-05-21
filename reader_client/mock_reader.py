import argparse
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def post_scan(api_url, reader_id, card_id):
    payload = json.dumps({"reader_id": reader_id, "card_id": card_id}).encode("utf-8")
    request = Request(
        f"{api_url.rstrip('/')}/scan",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def print_result(result):
    prefix = "ALLOWED" if result["allowed"] else "DENIED"
    print(
        f"{prefix} | card={result['card_id']} | reader={result['reader_id']} | "
        f"action={result['action']} | reason={result['reason']}"
    )


def main():
    parser = argparse.ArgumentParser(
        description="Mock NFC reader client for sending card taps to the Cards API."
    )
    parser.add_argument("--reader-id", required=True, help="Reader ID registered in the API.")
    parser.add_argument(
        "--api-url",
        default="http://127.0.0.1:8000",
        help="Cards API base URL.",
    )
    args = parser.parse_args()

    print(f"Reader client online | reader_id={args.reader_id} | api={args.api_url}")
    print("Type a card ID and press Enter. Type 'exit' to quit.")

    while True:
        card_id = input("card> ").strip()
        if card_id.lower() in {"exit", "quit"}:
            print("Reader client stopped.")
            break
        if not card_id:
            continue

        try:
            result = post_scan(args.api_url, args.reader_id, card_id)
            print_result(result)
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            print(f"API ERROR | status={exc.code} | {body}")
        except URLError as exc:
            print(f"CONNECTION ERROR | {exc.reason}")
        except TimeoutError:
            print("CONNECTION ERROR | request timed out")


if __name__ == "__main__":
    main()

