#!/usr/bin/env bash
# Apps Script bridge spike. Steps: login (owner, browser) -> deploy (script) -> authorize (owner, editor) -> test (script).
# Use a throwaway Google account. State lives in ./state (git-ignored): secret, script id, web app URL.
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
    echo "== gmail.search";  call "{\"secret\":\"$secret\",\"action\":\"gmail.search\",\"args\":{\"max\":3}}"
    echo "== gmail.draft";   call "{\"secret\":\"$secret\",\"action\":\"gmail.draft\",\"args\":{\"to\":\"test@example.com\",\"subject\":\"assistantOS spike\",\"body\":\"draft only\"}}"
    sid=$(call "{\"secret\":\"$secret\",\"action\":\"sheets.create\",\"args\":{\"title\":\"assistantOS spike sheet\"}}" | python3 -c 'import json,sys;print(json.load(sys.stdin)["result"])')
    call "{\"secret\":\"$secret\",\"action\":\"sheets.append\",\"args\":{\"id\":\"$sid\",\"row\":[\"ok\",42]}}" >/dev/null
    echo "== sheets.read";   call "{\"secret\":\"$secret\",\"action\":\"sheets.read\",\"args\":{\"id\":\"$sid\"}}"
    did=$(call "{\"secret\":\"$secret\",\"action\":\"docs.create\",\"args\":{\"title\":\"assistantOS spike doc\"}}" | python3 -c 'import json,sys;print(json.load(sys.stdin)["result"])')
    call "{\"secret\":\"$secret\",\"action\":\"docs.append\",\"args\":{\"id\":\"$did\",\"text\":\"hello from the bridge\"}}" >/dev/null
    echo "== docs.read";     call "{\"secret\":\"$secret\",\"action\":\"docs.read\",\"args\":{\"id\":\"$did\"}}"
    date -u +%FT%TZ > state/last-ok ;;
  *)
    echo "usage: $0 login|deploy|authorize|test"; exit 1 ;;
esac
