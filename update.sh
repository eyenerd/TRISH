#!/bin/bash

# 1. Generate a Granular Version Number (Year.Month.Day.HourMinute)
VERSION="v$(date +'%Y.%m.%d.%H%M')"

echo "🚀 Starting build for TRISH Unified Deck: $VERSION"

# Inject version string into index.html placeholder {{Version}}
if [ -f index.html ]; then
  # macOS sed in-place
  sed -i '' "s/{{Version}}/$VERSION/g" index.html 2>/dev/null || \
  # fallback for GNU sed
  sed -i "s/{{Version}}/$VERSION/g" index.html 2>/dev/null || true
  echo "🔖 Updated index.html with version: $VERSION"
fi

# Also handle subsequent runs by replacing any existing "Download TRISH ..." text
# inside the button span so the version updates even after {{Version}} is gone.
if [ -f index.html ]; then
  # macOS/BSD sed (extended regex)
  sed -i '' -E "s/(>Download TRISH)[^<]*(<\/span>)/\1 $VERSION\2/g" index.html 2>/dev/null || \
  # GNU sed fallback
  sed -i -E "s/(>Download TRISH)[^<]*(<\/span>)/\1 $VERSION\2/g" index.html 2>/dev/null || true
  echo "🔖 Ensured index.html button shows version: $VERSION"
fi

# Update trish-version meta tag and footer span for subsequent runs as well
if [ -f index.html ]; then
  # Use a small Python script to perform robust in-place replacements (cross-platform)
  python3 - <<PY
import io,sys,re
fn='index.html'
v=sys.argv[1] if len(sys.argv)>1 else '$VERSION'
with io.open(fn,'r',encoding='utf-8') as f:
    s=f.read()
# Replace meta trish-version content
s=re.sub(r'(<meta\s+name=["\']trish-version["\']\s+content=")[^"]*("[^>]*>)', r"\1"+v+r"\2", s, flags=re.IGNORECASE)
# Replace footer span inner text
s=re.sub(r'(<span[^>]*id=["\']trish-version["\'][^>]*>)[^<]*(</span>)', r"\1"+v+r"\2", s, flags=re.IGNORECASE)
# Replace Download TRISH button inner text (if present)
s=re.sub(r'(>Download TRISH)[^<]*(</span>)', r"\1 "+v+r"\2", s)
# Replace Anki download href and download attribute to point to versioned filename
s=re.sub(r'href=["\']TRISH_Anki/[^"\']*TRISH[^"\']*\.apkg["\']', 'href="TRISH_Anki/TRISH_'+v+'.apkg"', s)
s=re.sub(r'download=["\'][^"\']*["\']', 'download="TRISH_'+v+'.apkg"', s)
# Replace version label inside the download button (span.version-label)
s=re.sub(r'(<span[^>]*class=["\']version-label["\'][^>]*>)[^<]*(</span>)', r"\1"+v+r"\2", s, flags=re.IGNORECASE)
with io.open(fn,'w',encoding='utf-8') as f:
    f.write(s)
print('updated')
PY
  echo "🔖 Updated meta and footer version to: $VERSION"
fi

# 2. Convert Spreadsheets to TSV
# We assume the python script for TSV conversion works as before.

echo "Converting Sheets to TSV..."
python3 tsv-trish.py ./TRISH.ods "Fund"         -o ./TRISH_Sheets/fund.tsv
python3 tsv-trish.py ./TRISH.ods "Skin"         -o ./TRISH_Sheets/skin.tsv
python3 tsv-trish.py ./TRISH.ods "MSK"          -o ./TRISH_Sheets/msk.tsv
python3 tsv-trish.py ./TRISH.ods "NSHB"         -o ./TRISH_Sheets/nshb.tsv
python3 tsv-trish.py ./TRISH.ods "Cardio"       -o ./TRISH_Sheets/cardio.tsv
python3 tsv-trish.py ./TRISH.ods "Resp"         -o ./TRISH_Sheets/resp.tsv
python3 tsv-trish.py ./TRISH.ods "Renal"        -o ./TRISH_Sheets/renal.tsv
python3 tsv-trish.py ./TRISH.ods "EndoRepro"    -o ./TRISH_Sheets/endorepro.tsv
python3 tsv-trish.py ./TRISH.ods "Heme"         -o ./TRISH_Sheets/heme.tsv
python3 tsv-trish.py ./TRISH.ods "GI"           -o ./TRISH_Sheets/gi.tsv

# 3. Generate ONE Unified Anki Deck
# We use the wildcard *.tsv to pass all generated files at once.
echo "🔨 Generating Unified TRISH_$VERSION.apkg..."

python3 anki-trish.py \
  -i ./TRISH_Sheets/*.tsv \
  -d "TRISH" \
  -o ./TRISH_Anki/TRISH_$VERSION.apkg \
  -t "$VERSION"

# 4. Git Operations
echo "📦 Staging files..."
git add *

# Check if there are changes to commit
if git diff-index --quiet HEAD --; then
    echo "No changes detected. Skipping commit and tag."
else
    # Commit with the version number
    git commit -m "Update unified TRISH deck to $VERSION"
    
    # Tag the commit
    git tag -f "$VERSION"
    
    echo "✅ Committed and tagged $VERSION"
    
    # Push commits and tags
    git push origin main --tags
    echo "🚀 Pushed to remote."
fi