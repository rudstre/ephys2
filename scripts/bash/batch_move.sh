#!/usr/bin/env bash
#
# batch_move.sh
#
# Splits all .rhd files in a given directory into numbered batches of up to BATCH_SIZE files,
# ordered by filename (YYMMDD_HHMMSS), and will resume from any existing batch folders.
#
# Usage:
#   ./batch_move.sh /path/to/rhd_folder [batch_size] [prefix]
#
# Defaults:
#   batch_size = 10000
#   prefix     = batch
#

set -euo pipefail

# ———————— Parse arguments ————————
if [ $# -lt 1 ]; then
  echo "Usage: $0 <directory> [batch_size] [prefix]" >&2
  exit 1
fi

DIR="$1"
BATCH_SIZE="${2:-10000}"
PREFIX="${3:-batch}"

echo "→ Target directory: $DIR"
echo "→ Batch size      : $BATCH_SIZE"
echo "→ Folder prefix   : $PREFIX"
echo

# ———————— Enter the target directory ————————
cd "$DIR"
echo "Changed into $(pwd)"
echo

# ———————— Detect existing batches ————————
echo "Scanning for existing batch directories (${PREFIX}_###)..."
existing=()
for d in ${PREFIX}_*; do
  if [[ -d "$d" && "$d" =~ ^${PREFIX}_[0-9]{3}$ ]]; then
    existing+=("$d")
  fi
done

if (( ${#existing[@]} > 0 )); then
  echo "✅  Found ${#existing[@]} existing batch dirs: ${existing[*]}"
  # find highest numeric suffix
  max=0
  for d in "${existing[@]}"; do
    num=$((10#${d##*_}))
    (( num > max )) && max=$num
  done
  batch_num=$max
  last_dir=$(printf "%s_%03d" "$PREFIX" "$batch_num")
  existing_count=$(find "$last_dir" -maxdepth 1 -type f -name '*.rhd' | wc -l)
  echo "Last batch is '$last_dir' with $existing_count files in it."

  if (( existing_count >= BATCH_SIZE )); then
    batch_num=$(( max + 1 ))
    file_counter=0
    echo "Last batch is full; will start new batch $(printf "%03d" "$batch_num")."
  else
    file_counter=$existing_count
    echo "Resuming batch $(printf "%03d" "$batch_num") (next file will be #$((file_counter+1)) of $BATCH_SIZE)."
  fi
else
  echo "⚠️  No existing batch dirs found; starting at batch 001."
  batch_num=1
  file_counter=0
fi
echo

# ———————— Gather and sort remaining .rhd files ————————
echo "Listing all .rhd files in base directory, sorted by timestamp..."
mapfile -t files < <(printf "%s\n" *.rhd | sort)
total=${#files[@]}

if (( total == 0 )); then
  echo "⚠️  No .rhd files left in $DIR – nothing to do."
  exit 0
fi

echo "✅  $total files to process."
echo

# ———————— Move into batches ————————
for src in "${files[@]}"; do
  dir=$(printf "%s_%03d" "$PREFIX" "$batch_num")

  # create dir if needed (either new batch or first resume)
  if (( file_counter == 0 )) && [ ! -d "$dir" ]; then
    echo "=== Creating directory '$dir' ==="
    mkdir -p "$dir"
  fi

  echo "Moving '$src' → '$dir/'"
  mv -- "$src" "$dir/"

  file_counter=$(( file_counter + 1 ))

  # if batch is now full, roll over to the next
  if (( file_counter >= BATCH_SIZE )); then
    echo "+++ Batch $(printf "%03d" "$batch_num") is now full ($file_counter files). +++"
    batch_num=$(( batch_num + 1 ))
    file_counter=0
    echo "Next batch will be $(printf "%03d" "$batch_num")."
    echo
  fi
done

finished_batches=$(( batch_num - ( file_counter == 0 ? 1 : 0 ) ))
echo
echo "🎉 Done! Processed $total files into $finished_batches batch folders."
