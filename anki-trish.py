import argparse
import genanki
import html
import pandas as pd
import sys
import os
import hashlib
import re

# --- Helpers ---

def get_stable_id(string_val):
    """
    Generates a deterministic 32-bit integer ID from a string.
    Ensures that Deck and Model IDs remain constant across runs.
    """
    hash_bytes = hashlib.sha256(string_val.encode('utf-8')).digest()
    return int.from_bytes(hash_bytes[:4], byteorder='big') & (1 << 31) - 1

def clean_for_tts(text):
    """
    Removes HTML tags and converts newlines to punctuation for better speech flow.
    """
    # Replace newlines with a period and space so the voice pauses
    text = str(text).replace('\n', '. ')
    # Remove HTML tags
    text = re.sub('<[^<]+?>', '', text)
    return text.strip()

def clean_tag(txt):
    return txt.strip().replace(" ", "_").replace("&", "and")

def main():
    # 1. Setup CLI Argument Parser
    parser = argparse.ArgumentParser(description="Convert multiple TSVs to a single Unified Anki Deck.")
    
    parser.add_argument('-i', '--input', required=True, nargs='+', help="List of input TSV files")
    parser.add_argument('-d', '--deck-name', default="TRISH", help="Name of the Anki Deck")
    parser.add_argument('-o', '--output', help="Output filename")
    parser.add_argument('-v', '--voice', default="Apple_Evan_(Enhanced)", help="Preferred TTS voice.")
    parser.add_argument('-t', '--tag', default="Unknown", help="Version string (e.g., v2024.01.09)")

    args = parser.parse_args()

    # 2. Setup Variables
    deck_title = args.deck_name
    
    if args.output:
        output_file = args.output
    else:
        # Default output name
        safe_name = "".join([c if c.isalnum() else "_" for c in deck_title])
        output_file = f"{safe_name}.apkg"

    # --- 3. Load, Merge, and Deduplicate Data ---
    print(f"📦 Loading {len(args.input)} files for Unified Deck '{deck_title}'...")

    # Dictionary to store unique conditions
    # Key: Condition name (lowercase)
    # Value: { 'row': pandas Series, 'blocks': set of strings }
    merged_data = {}
    
    # Keep track of column structure from the first valid file
    columns = None

    for filepath in args.input:
        if not os.path.exists(filepath):
            print(f"⚠️ Warning: File '{filepath}' not found. Skipping.")
            continue
            
        # Extract Block Name from filename (e.g., "msk.tsv" -> "MSK")
        filename = os.path.basename(filepath)
        block_name = os.path.splitext(filename)[0].upper() # e.g., MSK, CARDIO
        
        try:
            df = pd.read_csv(filepath, sep='\t').fillna('')
        except Exception as e:
            print(f"❌ Error reading {filepath}: {e}")
            continue

        if columns is None and not df.empty:
            columns = df.columns
        
        if df.empty:
            continue

        primary_col = df.columns[0] # Assumes "Condition" is the first column

        for _, row in df.iterrows():
            condition_raw = str(row[primary_col]).strip()
            if not condition_raw: 
                continue
                
            condition_key = condition_raw.lower()
            
            if condition_key not in merged_data:
                # First time seeing this condition: Save row data and start block set
                merged_data[condition_key] = {
                    'row': row,
                    'blocks': {block_name} 
                }
            else:
                # Duplicate found! We keep the existing data, but add the new block tag
                merged_data[condition_key]['blocks'].add(block_name)

    unique_count = len(merged_data)
    print(f"✅ Processed {unique_count} unique conditions (deduplicated).")
    print(f"🔨 Generating deck '{deck_title}' (Version: {args.tag})...")

    if unique_count == 0 or columns is None:
        print("❌ No data found. Exiting.")
        return

    # 4. Construct Voice List
    user_voice = args.voice.replace(" ", "_")
    fallbacks = ["Apple_Evan_(Enhanced)", "Microsoft_David", "Microsoft_Zira", "Google_US_English"]
    voice_list_arr = [user_voice] + [v for v in fallbacks if v != user_voice]
    voice_string = ",".join(voice_list_arr)

    # 5. Define Anki Model
    model_id = get_stable_id(f"{deck_title}_Unified_Model_v4")
    
    css = """
        .card { font-family: arial; font-size: 20px; text-align: center; color: black; background-color: white; }
        .label { font-size: 16px; color: #666; margin-bottom: 10px; }
        .answer { margin-top: 20px; }
        .warning { color: red; font-weight: bold; font-size: 16px; border: 2px solid red; padding: 10px; margin-top: 15px; display: inline-block;}
        .more-info { margin-top: 15px; font-size: 16px; }
        .more-info a { color: #007bff; text-decoration: none; font-weight: bold; }
        .tags-display { font-size: 12px; color: #aaa; margin-top: 30px; font-style: italic; }
    """

    my_model = genanki.Model(
        model_id,
        f'{deck_title} TTS Model v4',
        fields=[
            {'name': 'Question_Display'}, 
            {'name': 'Answer_Display'},   
            {'name': 'Question_TTS'},     
            {'name': 'Answer_TTS'},       
            {'name': 'NeverMiss'},        
            {'name': 'MoreInfo'},
            {'name': 'BlockTags'},
        ],
        templates=[
            {
                'name': 'Card 1',
                'qfmt': '''
                    {{Question_Display}}
                    <div style="display:none">{{tts en_US voices=%s:Question_TTS}}</div>
                ''' % voice_string,
                'afmt': '''
                    {{FrontSide}}
                    <hr id=answer>
                    <div class='answer'>{{Answer_Display}}</div>
                    {{#NeverMiss}}<br><br><div class='warning'>Never Miss</div>{{/NeverMiss}}
                    
                    {{#MoreInfo}}
                        <div class='more-info'>
                            <br><br>
                            <a href="{{MoreInfo}}">📖 Read More</a>
                        </div>
                    {{/MoreInfo}}
                    
                    <div class='tags-display'>{{BlockTags}}</div>

                    <div style="display:none">{{tts en_US voices=%s:Answer_TTS}}</div>
                ''' % voice_string,
            },
        ],
        css=css
    )

    deck_id = get_stable_id(deck_title)
    my_deck = genanki.Deck(deck_id, deck_title)
    
    base_tag_prefix = f"TRISH"

    # --- Add Version Info Note ---
    print(f"Embedding version info: {args.tag}")
    info_guid = genanki.guid_for("DECK_INFO_CARD", deck_title)
    
    info_note = genanki.Note(
        model=my_model,
        fields=[
            f"<b>{deck_title}</b><br>Version Information",
            f"Last Updated: <b>{args.tag}</b><br>Unique Conditions: {unique_count}<br><br>Check for updates regularly.",
            "Deck Version Information",
            f"Updated to version {args.tag}",
            "",
            "",
            ""
        ],
        tags=[f"{base_tag_prefix}::MetaData"],
        guid=info_guid
    )
    my_deck.add_note(info_note)

    # 6. Generate Notes from Merged Data
    primary_col = columns[0] # Condition

    for condition_key, data in merged_data.items():
        row = data['row']
        blocks = data['blocks'] 
        
        condition = str(row[primary_col])
        never_miss = str(row['Never Miss']) if 'Never Miss' in row else ''
        
        more_info_url = str(row['More Info']) if 'More Info' in row else ''
        if not more_info_url.strip():
            more_info_url = ''

        block_tags_list = [f"{base_tag_prefix}::Blocks::{clean_tag(b)}" for b in sorted(blocks)]
        block_display_str = ", ".join(sorted(blocks))

        for col in columns:
            if col == primary_col or col == "Never Miss" or col == "More Info":
                continue

            val = str(row[col])
            if not val.strip():
                continue

            # --- Logic for Prompts & Text ---
            if col == "Salient Signs & Symptoms":
                prompt_html, prompt_text = "What are the <u>Salient Signs & Symptoms</u> of", "What are the Salient Signs and Symptoms of"
            elif col == "Diagnostics":
                prompt_html, prompt_text = "How would you <u>Diagnose</u>", "How would you Diagnose"
            elif col == "USMLE Classic Presentation":
                prompt_html, prompt_text = "What <u>condition</u> presents as:", "What condition presents as"
            else:
                prompt_html, prompt_text = f"What is the <u>{col}</u> of", f"What is the {col} of"

            # --- CHANGED HERE: Removed html.escape() for the answer field ---
            # We assume the spreadsheet contains valid HTML (or plain text) that you want rendered as-is.
            val_display = str(val).replace('\n', '<br>')
            
            # We keep escaping the condition to ensure the title isn't broken by accidental chars
            cond_display = html.escape(condition)
            
            # TTS cleaning still happens here, so <strong> tags won't be spoken aloud
            val_tts = clean_for_tts(val)
            cond_tts = clean_for_tts(condition)

            current_tags = block_tags_list.copy()
            current_tags.append(f"{base_tag_prefix}::Conditions::{clean_tag(condition)}")

            if col == "USMLE Classic Presentation":
                # REVERSED CARD
                q_disp = f"<div class='label'>{prompt_html}</div><br>{val_display}"
                a_disp = cond_display
                q_tts = f"{prompt_text}: {val_tts}"
                a_tts = cond_tts
                
                guid = genanki.guid_for(deck_title, condition, "Presentation")
                current_tags.append(f"{base_tag_prefix}::Presentation")

            else:
                # FORWARD CARD
                q_disp = f"<div class='label'>{prompt_html}</div><br>{cond_display}"
                a_disp = val_display
                q_tts = f"{prompt_text} {cond_tts}?"
                a_tts = val_tts

                guid = genanki.guid_for(deck_title, condition, col)
                current_tags.append(f"{base_tag_prefix}::{clean_tag(col)}")

            if never_miss and never_miss.strip().startswith('Y'):
                current_tags.append(f"{base_tag_prefix}::Never_Miss")

            note = genanki.Note(
                model=my_model,
                fields=[
                    q_disp, 
                    a_disp, 
                    q_tts, 
                    a_tts, 
                    never_miss,
                    more_info_url,
                    block_display_str
                ],
                tags=current_tags,
                guid=guid
            )
            my_deck.add_note(note)

    # 7. Export
    genanki.Package(my_deck).write_to_file(output_file)
    print(f"Voice: {voice_string.split(',')[0]} (plus fallbacks)")
    print(f"Success! Unified Deck saved to: {output_file}")

if __name__ == "__main__":
    main()