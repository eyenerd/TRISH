# Totally-Rad Illness Script Hub (TRISH)

## Purpose
**TRISH** (the Totally-Rad Illness Script Hub) is one of my primary medical school tools. I believe that coalescing information into illness schemas ("illness scripts" as physicians call them) gets me thinking like a doctor as I'm studying.

Perhaps the best study feature is that TRISH is able to turn illness scripts into Anki cards, complete with tags and text-to-speech.

As I create TRISH and update it, you will be able to go to this GitHub page for the most up-to-date version. You can view the up-to-date spreadsheet online there, as well as download the updated Anki decks. I have built in a feature that allows you to add new cards and update old ones without losing your Anki SRS history.

Creation of the content is assissted by OpenEvidence. If you want to see the prompt I use, please refer to `oe_prompt.txt`. If you use this prompt yourself, note that OpenEvidence seems to max out with about 6 conditions at a time.

## Contents
This repository contains everything needed for TRISH:
- `TRISH.ods`, aka the spreadsheet that is the source of truth for TRISH
- `tsv-trish.py`, which converts each page in `TRISH.ods` into a `.tsv` file
- `anki-trish.py`, which converts each `.tsv` file into an Anki deck (`.apkg`)
- `update.sh`, which will automatically update and push all changes (so only `TRISH.ods` needs to be changed)
