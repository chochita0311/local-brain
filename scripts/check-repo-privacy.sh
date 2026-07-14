#!/usr/bin/env bash

set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

if ! command -v rg >/dev/null 2>&1; then
  printf 'privacy check requires ripgrep (rg)\n' >&2
  exit 2
fi

candidate_list="$(mktemp)"
content_list="$(mktemp)"
regex_patterns="$(mktemp)"
fixed_patterns="$(mktemp)"
local_patterns="$(mktemp)"
matches="$(mktemp)"

cleanup() {
  rm -f "$candidate_list" "$content_list" "$regex_patterns" "$fixed_patterns" "$local_patterns" "$matches"
}
trap cleanup EXIT

git ls-files --cached --others --exclude-standard -z > "$candidate_list"

failed=0

is_allowlisted() {
  local candidate="$1"
  [[ -f .privacy-allowlist ]] || return 1
  awk 'NF && $1 !~ /^#/ { print }' .privacy-allowlist | grep -Fqx -- "$candidate"
}

while IFS= read -r -d '' file; do
  case "$file" in
    .env|.env.*)
      if [[ "$file" != ".env.example" ]]; then
        printf 'forbidden environment file: %s\n' "$file" >&2
        failed=1
      fi
      ;;
    data/*|*/data/*|runs/*|*/runs/*|exports/*|*/exports/*|artifacts/*|*/artifacts/*|playwright-report/*|*/playwright-report/*|test-results/*|*/test-results/*)
      printf 'forbidden runtime artifact: %s\n' "$file" >&2
      failed=1
      ;;
    *.db|*.db-*|*.sqlite|*.sqlite3|*.jsonl|*.log|*.har|*.trace|*.key|*.pem|*.p8|*.p12|*.mobileprovision)
      printf 'forbidden sensitive file type: %s\n' "$file" >&2
      failed=1
      ;;
    *.png|*.jpg|*.jpeg|*.webp|*.gif|*.pdf|*.zip|*.tar|*.gz|*.7z|*.woff|*.woff2|*.ttf|*.otf)
      if ! is_allowlisted "$file"; then
        printf 'unreviewed binary or media file: %s\n' "$file" >&2
        printf 'add the reviewed path to .privacy-allowlist before committing it\n' >&2
        failed=1
      fi
      ;;
  esac

  if [[ "$file" != "scripts/check-repo-privacy.sh" ]]; then
    printf '%s\0' "$file" >> "$content_list"
  fi
done < "$candidate_list"

if [[ "$failed" -ne 0 ]]; then
  exit 1
fi

{
  printf '%s\n' '/Users/[[:alnum:]_.-]+/'
  printf '%s\n' '[[:alnum:]._%+-]+@[[:alnum:].-]+\.[A-Za-z]{2,}'
  printf '%s\n' 'https://[^[:space:])]*(slack\.com|atlassian\.net)'
  printf '%s\n' 'AKIA[0-9A-Z]{16}'
  printf '%s\n' 'xox[baprs]-[A-Za-z0-9-]+'
  printf '%s\n' 'sk-ant-[A-Za-z0-9_-]{16,}'
  printf '%s\n' 'gh[pousr]_[A-Za-z0-9_]{20,}'
  printf '%s\n' '-----BEGIN (RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----'
} > "$regex_patterns"

printf '%s\n' "$HOME/" >> "$fixed_patterns"
git_email="$(git config --get user.email || true)"
git_name="$(git config --get user.name || true)"
[[ -n "$git_email" ]] && printf '%s\n' "$git_email" >> "$fixed_patterns"
[[ -n "$git_name" ]] && printf '%s\n' "$git_name" >> "$fixed_patterns"

if [[ -f .privacy-patterns.local ]]; then
  while IFS= read -r pattern; do
    [[ -z "$pattern" || "$pattern" == \#* ]] && continue
    printf '%s\n' "$pattern" >> "$local_patterns"
  done < .privacy-patterns.local
fi

if [[ -s "$content_list" ]]; then
  xargs -0 rg -l --no-messages -f "$regex_patterns" -- < "$content_list" > "$matches" || true
  if [[ -s "$fixed_patterns" ]]; then
    xargs -0 rg -l -F --no-messages -f "$fixed_patterns" -- < "$content_list" >> "$matches" || true
  fi
  if [[ -s "$local_patterns" ]]; then
    xargs -0 rg -l -F -i -w --no-messages -f "$local_patterns" -- < "$content_list" >> "$matches" || true
  fi
fi

if [[ -s "$matches" ]]; then
  printf 'privacy check found sensitive content patterns in:\n' >&2
  sort -u "$matches" >&2
  printf 'only file paths are shown; inspect matches locally before committing\n' >&2
  exit 1
fi

candidate_count="$(tr -cd '\0' < "$candidate_list" | wc -c | tr -d ' ')"
printf 'privacy check passed (%s candidate files)\n' "$candidate_count"
