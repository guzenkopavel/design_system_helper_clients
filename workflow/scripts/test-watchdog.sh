#!/usr/bin/env bash
set -u

max_seconds=300
stall_seconds=90
max_output_lines=4000
child_pid=""
output_file=""

kill_tree() {
  local pid="$1" child
  while read -r child; do
    [ -n "$child" ] && kill_tree "$child"
  done < <(pgrep -P "$pid" 2>/dev/null || true)
  kill -TERM "$pid" 2>/dev/null || true
}

cleanup() {
  if [ -n "$child_pid" ] && kill -0 "$child_pid" 2>/dev/null; then
    kill_tree "$child_pid"
    wait "$child_pid" 2>/dev/null || true
  fi
  [ -n "$output_file" ] && rm -f "$output_file"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

self_test() {
  local script="$1" status
  bash "$script" --max-seconds 3 --stall-seconds 1 --max-output-lines 10 -- bash -c 'printf "pass\n"'
  [ "$?" -eq 0 ] || return 1
  bash "$script" --max-seconds 3 --stall-seconds 1 --max-output-lines 10 -- bash -c 'printf "fail\n"; exit 7'
  status=$?; [ "$status" -eq 7 ] || return 1
  bash "$script" --max-seconds 3 --stall-seconds 1 --max-output-lines 2 -- bash -c 'printf "1\n2\n3\n"'
  status=$?; [ "$status" -eq 125 ] || return 1
  bash "$script" --max-seconds 4 --stall-seconds 1 --max-output-lines 10 -- bash -c 'sleep 3'
  status=$?; [ "$status" -eq 126 ] || return 1
  bash "$script" --max-seconds 1 --stall-seconds 0 --max-output-lines 10 -- bash -c 'sleep 3'
  status=$?; [ "$status" -eq 124 ] || return 1
  printf 'test-watchdog self-test: PASS (pass/fail/output/stall/max)\n'
}

if [ "${1:-}" = "--self-test" ]; then
  self_test "$0"
  exit $?
fi

while [ "$#" -gt 0 ]; do
  case "$1" in
    --max-seconds) max_seconds="$2"; shift 2 ;;
    --stall-seconds) stall_seconds="$2"; shift 2 ;;
    --max-output-lines) max_output_lines="$2"; shift 2 ;;
    --) shift; break ;;
    *) printf 'BLOCKED: unknown watchdog argument: %s\n' "$1" >&2; exit 2 ;;
  esac
done
[ "$#" -gt 0 ] || { printf 'BLOCKED: watchdog requires a command\n' >&2; exit 2; }
for value in "$max_seconds" "$stall_seconds" "$max_output_lines"; do
  [[ "$value" =~ ^[0-9]+$ ]] || { printf 'BLOCKED: watchdog limits must be integers\n' >&2; exit 2; }
done
[ "$max_seconds" -gt 0 ] && [ "$max_output_lines" -gt 0 ] || {
  printf 'BLOCKED: max-seconds and max-output-lines must be positive\n' >&2; exit 2;
}

output_file="$(mktemp "${TMPDIR:-/tmp}/test-watchdog.XXXXXX")"
"$@" >"$output_file" 2>&1 &
child_pid=$!
start=$SECONDS
last_progress=$SECONDS
last_lines=0
watchdog_status=0

while kill -0 "$child_pid" 2>/dev/null; do
  lines=$(wc -l <"$output_file" | tr -d ' ')
  if [ "$lines" -gt "$max_output_lines" ]; then
    watchdog_status=125; break
  fi
  if [ "$lines" -ne "$last_lines" ]; then
    last_lines=$lines; last_progress=$SECONDS
  fi
  if [ "$stall_seconds" -gt 0 ] && [ $((SECONDS - last_progress)) -ge "$stall_seconds" ]; then
    watchdog_status=126; break
  fi
  if [ $((SECONDS - start)) -ge "$max_seconds" ]; then
    watchdog_status=124; break
  fi
  sleep 0.1
done

if [ "$watchdog_status" -ne 0 ]; then
  kill_tree "$child_pid"
  wait "$child_pid" 2>/dev/null || true
  child_pid=""
else
  wait "$child_pid"; command_status=$?
  child_pid=""
  lines=$(wc -l <"$output_file" | tr -d ' ')
  if [ "$lines" -gt "$max_output_lines" ]; then
    watchdog_status=125
  else
    watchdog_status=$command_status
  fi
fi
sed -n "1,${max_output_lines}p" "$output_file"
case "$watchdog_status" in
  124) printf 'WATCHDOG: maximum runtime exceeded (%ss)\n' "$max_seconds" >&2 ;;
  125) printf 'WATCHDOG: output limit exceeded (%s lines)\n' "$max_output_lines" >&2 ;;
  126) printf 'WATCHDOG: no output progress for %ss\n' "$stall_seconds" >&2 ;;
esac
exit "$watchdog_status"
