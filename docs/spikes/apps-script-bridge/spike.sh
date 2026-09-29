#!/usr/bin/env bash
# Apps Script bridge spike. Steps: login (owner, browser) -> deploy (script) -> authorize (owner, editor) -> test (script).
# Runs on a customer's real account (Ian, 2026-09-29): read/draft only, prints no mail content, `cleanup` removes what it created. State lives in ./state (git-ignored): secret, script id, web app URL.
set -euo pipefail
cd "$(dirname "$0")"
CLASP="npx -y @google/clasp@3.4.1"
mkdir -p state

case "${1:-}" in
  login)
    $CLASP login ;;
  deploy)
    [ -f state/secret ] || openssl rand -hex 16 > state/secret
    printf 'var SECRET = "%s";\n' "$(cat state/secret)" > src/Secret.gs
    [ -f .clasp.json ] || $CLASP create-script --type standalone --title "assistantOS bridge (spike)" --rootDir src
    $CLASP push --force
    dep=$($CLASP create-deployment --description spike | grep -oE 'AKfy[A-Za-z0-9_-]+' | head -1)
    echo "https://script.google.com/macros/s/$dep/exec" > state/url
    echo "web app: $(cat state/url)" ;;
  authorize)
    echo "In the editor: pick 'authorize' in the function menu -> Run -> accept (Advanced -> Go to ... if Google warns)."
    $CLASP open-script ;;
  test)
    url=$(cat state/url); secret=$(cat state/secret)
    call() { curl -sL -H 'Content-Type: application/json' -d "$1" "$url"; echo; }
    echo "== no secret (must be unauthorized)";  call '{"action":"gmail.search"}'
    echo "== wrong secret";                      call '{"secret":"x","action":"gmail.search"}'
    echo "== GET";                                curl -sL "$url"; echo
    # a customer account: print counts and field names only, never mail content
    echo "== gmail.search";  call "{\"secret\":\"$secret\",\"action\":\"gmail.search\",\"args\":{\"max\":3}}" | python3 -c 'import json,sys;r=json.load(sys.stdin);print({"ok":r["ok"],"threads":len(r.get("result") or []),"fields":sorted((r.get("result") or [{}])[0].keys()),"error":r.get("error")})'
    echo "== gmail.draft";   call "{\"secret\":\"$secret\",\"action\":\"gmail.draft\",\"args\":{\"to\":\"test@example.com\",\"subject\":\"assistantOS spike\",\"body\":\"draft only\"}}" | tee /dev/stderr | python3 -c 'import json,sys;print(json.load(sys.stdin)["result"])' > state/draft
    sid=$(call "{\"secret\":\"$secret\",\"action\":\"sheets.create\",\"args\":{\"title\":\"assistantOS spike sheet\"}}" | python3 -c 'import json,sys;print(json.load(sys.stdin)["result"])')
    echo "$sid" > state/sheet
    call "{\"secret\":\"$secret\",\"action\":\"sheets.append\",\"args\":{\"id\":\"$sid\",\"row\":[\"ok\",42]}}" >/dev/null
    echo "== sheets.read";   call "{\"secret\":\"$secret\",\"action\":\"sheets.read\",\"args\":{\"id\":\"$sid\"}}"
    did=$(call "{\"secret\":\"$secret\",\"action\":\"docs.create\",\"args\":{\"title\":\"assistantOS spike doc\"}}" | python3 -c 'import json,sys;print(json.load(sys.stdin)["result"])')
    echo "$did" > state/doc
    call "{\"secret\":\"$secret\",\"action\":\"docs.append\",\"args\":{\"id\":\"$did\",\"text\":\"hello from the bridge\"}}" >/dev/null
    echo "== docs.read";     call "{\"secret\":\"$secret\",\"action\":\"docs.read\",\"args\":{\"id\":\"$did\"}}"
    date -u +%FT%TZ > state/last-ok ;;
  cleanup)
    # remove everything the test created, take the web app down, forget the account on this Mac
    url=$(cat state/url); secret=$(cat state/secret)
    call() { curl -sL -H 'Content-Type: application/json' -d "$1" "$url"; echo; }
    [ -f state/draft ] && call "{\"secret\":\"$secret\",\"action\":\"gmail.deleteDraft\",\"args\":{\"id\":\"$(cat state/draft)\"}}"
    for f in sheet doc; do [ -f state/$f ] && call "{\"secret\":\"$secret\",\"action\":\"drive.trash\",\"args\":{\"id\":\"$(cat state/$f)\"}}"; done
    [ "${2:-}" = keep ] || $CLASP delete-deployment --all || true   # `cleanup keep`: web app stays up for the 7-day check
    $CLASP logout
    echo "Left in the account: the script project 'assistantOS bridge (spike)' (delete at script.google.com if not kept)." ;;
  check)
    # no Google login needed: proves the web app still has access (run 8+ days after authorize)
    url=$(cat state/url); secret=$(cat state/secret)
    curl -sL -H 'Content-Type: application/json' -d "{\"secret\":\"$secret\",\"action\":\"gmail.search\",\"args\":{\"max\":1}}" "$url" | python3 -c 'import json,sys;r=json.load(sys.stdin);print({"ok":r["ok"],"threads":len(r.get("result") or []),"error":r.get("error")})' ;;
  *)
    echo "usage: $0 login|deploy|authorize|test|cleanup [keep]|check"; exit 1 ;;
esac
