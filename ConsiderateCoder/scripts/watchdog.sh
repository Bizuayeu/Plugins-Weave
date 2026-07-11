#!/bin/bash
# watchdog.sh — 対象ディレクトリへの書き込み沈黙を検知して STALLED を 1 行発報する
#
# usage: watchdog.sh <dir> [threshold_sec=1200] [interval_sec=60]
#
# /outsource の bg 起動（Phase 3b）で Monitor から張る死活監視の決定論部:
#   Monitor(command: "bash <plugin>/scripts/watchdog.sh <対象リポ> 1200 60", persistent: true)
# 各 stdout 行が Monitor のイベントとして親（communicator）を起こす。通常時は無音、
# 沈黙検知時のみ STALLED を出力して exit する（イベント過多の抑制）。
#
# 設計メモ（2026-07-11 奥宮 v0.1 実装での実測を焼き込み）:
# - 沈黙の起点は「監視開始時刻」と「最終書き込み mtime」の新しい方を取る。
#   監視開始前からの古い mtime に初回ループで即発報する偽陽性を防ぐ。
# - STALLED はエージェントの死を意味しない（読み取り・思考中はファイルが動かない）。
#   受け手は TaskOutput で生死を実測してから静観／蘇生を判断する（二段判定）。
# - 閾値既定 1200 秒（20 分）: worker の初動（検分・思考）は 15 分を超えうる。
DIR="${1:?usage: watchdog.sh <dir> [threshold_sec] [interval_sec]}"
THRESH="${2:-1200}"
INT="${3:-60}"
START=$(date +%s)
while true; do
  LAST=$(find "$DIR" -type f -not -path "*/node_modules/*" -not -path "*/.git/*" -printf "%T@\n" 2>/dev/null | sort -rn | head -1)
  LAST=${LAST%.*}
  NOW=$(date +%s)
  BASE=$START
  if [ -n "$LAST" ] && [ "$LAST" -gt "$BASE" ]; then
    BASE=$LAST
  fi
  SILENT=$((NOW - BASE))
  if [ "$SILENT" -ge "$THRESH" ]; then
    echo "STALLED silent=${SILENT}s last_write_epoch=${LAST:-none}"
    exit 0
  fi
  sleep "$INT"
done
