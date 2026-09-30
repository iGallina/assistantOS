"""Stands in for `claude` / `codex` in tests. FAKE_REPLY = answer JSON | "quota" | "garbage"; FAKE_ARGV = file to record argv."""
import json, os, sys

kind, args = sys.argv[1], sys.argv[2:]
sys.stdin.read()
if os.environ.get("FAKE_ARGV"):
    open(os.environ["FAKE_ARGV"], "w", encoding="utf-8").write(json.dumps(args))
reply = os.environ["FAKE_REPLY"]
if reply == "quota":
    print("You've hit your usage limit. Try again later.", file=sys.stderr)
    sys.exit(1)
if kind == "claude":
    print(reply if reply == "garbage" else json.dumps({"is_error": False, "structured_output": json.loads(reply)}))
else:
    open(args[args.index("-o") + 1], "w", encoding="utf-8").write(reply)
