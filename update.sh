#!/bin/bash

# 1. Generate a Granular Version Number (Year.Month.Day.HourMinute)
# Example output: v2024.01.09.1530 (3:30 PM)
VERSION="v$(date +'%Y.%m.%d.%H%M')"

echo "🚀 Starting build for TRISH version: $VERSION"

# 2. Run the build commands, passing the version flag
# Note: Added -t "$VERSION" to all anki-trish.py calls

echo "Building Fundamentals..."
python3 tsv-trish.py ./TRISH_Sheets/TRISH.ods "Fundamentals" -o ./TRISH_Sheets/tsv/fundamentals.tsv && \
python3 anki-trish.py -i ./TRISH_Sheets/tsv/fundamentals.tsv -d Fundamentals -o ./TRISH_Anki/Fundamentals.apkg -t "$VERSION"

echo "Building Skin..."
python3 tsv-trish.py ./TRISH_Sheets/TRISH.ods "Skin" -o ./TRISH_Sheets/tsv/skin.tsv && \
python3 anki-trish.py -i ./TRISH_Sheets/tsv/skin.tsv -d Skin -o ./TRISH_Anki/Skin.apkg -t "$VERSION"

echo "Building MSK..."
python3 tsv-trish.py ./TRISH_Sheets/TRISH.ods "MSK" -o ./TRISH_Sheets/tsv/msk.tsv && \
python3 anki-trish.py -i ./TRISH_Sheets/tsv/msk.tsv -d MSK -o ./TRISH_Anki/MSK.apkg -t "$VERSION"

echo "Building NSHB..."
python3 tsv-trish.py ./TRISH_Sheets/TRISH.ods "NSHB" -o ./TRISH_Sheets/tsv/nshb.tsv && \
python3 anki-trish.py -i ./TRISH_Sheets/tsv/nshb.tsv -d NSHB -o ./TRISH_Anki/NSHB.apkg -t "$VERSION"

echo "Building Cardio..."
python3 tsv-trish.py ./TRISH_Sheets/TRISH.ods "Cardio" -o ./TRISH_Sheets/tsv/cardio.tsv && \
python3 anki-trish.py -i ./TRISH_Sheets/tsv/cardio.tsv -d Cardio -o ./TRISH_Anki/Cardio.apkg -t "$VERSION"

echo "Building Resp..."
python3 tsv-trish.py ./TRISH_Sheets/TRISH.ods "Resp" -o ./TRISH_Sheets/tsv/resp.tsv && \
python3 anki-trish.py -i ./TRISH_Sheets/tsv/resp.tsv -d Resp -o ./TRISH_Anki/Resp.apkg -t "$VERSION"

echo "Building Renal..."
python3 tsv-trish.py ./TRISH_Sheets/TRISH.ods "Renal" -o ./TRISH_Sheets/tsv/renal.tsv && \
python3 anki-trish.py -i ./TRISH_Sheets/tsv/renal.tsv -d Renal -o ./TRISH_Anki/Renal.apkg -t "$VERSION"

echo "Building EndoRepro..."
python3 tsv-trish.py ./TRISH_Sheets/TRISH.ods "EndoRepro" -o ./TRISH_Sheets/tsv/endorepro.tsv && \
python3 anki-trish.py -i ./TRISH_Sheets/tsv/endorepro.tsv -d EndoRepro -o ./TRISH_Anki/EndoRepro.apkg -t "$VERSION"

echo "Building Heme..."
python3 tsv-trish.py ./TRISH_Sheets/TRISH.ods "Heme" -o ./TRISH_Sheets/tsv/heme.tsv && \
python3 anki-trish.py -i ./TRISH_Sheets/tsv/heme.tsv -d Heme -o ./TRISH_Anki/Heme.apkg -t "$VERSION"

echo "Building GI..."
python3 tsv-trish.py ./TRISH_Sheets/TRISH.ods "GI" -o ./TRISH_Sheets/tsv/gi.tsv && \
python3 anki-trish.py -i ./TRISH_Sheets/tsv/gi.tsv -d GI -o ./TRISH_Anki/GI.apkg -t "$VERSION"

# 3. Git Operations
echo "📦 Staging files..."
git add *

# Check if there are changes to commit
if git diff-index --quiet HEAD --; then
    echo "No changes detected. Skipping commit and tag."
else
    # Commit with the version number
    git commit -m "Update decks to $VERSION"
    
    # Tag the commit
    # -f forces the tag update if you run it multiple times a day (optional, 
    # remove -f if you want unique tags for every run in a day)
    git tag -f "$VERSION"
    
    echo "✅ Committed and tagged $VERSION"
    
    # Push commits and tags
    git push origin main --tags
    echo "🚀 Pushed to remote."
fi