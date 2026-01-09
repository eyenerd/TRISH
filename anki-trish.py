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

def main():
    # 1. Setup CLI Argument Parser
    parser = argparse.ArgumentParser(description="Convert TSV to Anki with Full Sentence TTS.")
    
    parser.add_argument('-i', '--input', required=True, help="Path to input TSV")
    parser.add_argument('-d', '--deck-name', required=True, help="Name of the Anki Deck")
    parser.add_argument('-o', '--output', help="Output filename")
    parser.add_argument('-v', '--voice', default="Apple_Evan_(Enhanced)", help="Preferred TTS voice. Defaults to Apple Evan.")
    parser.add_argument('-t', '--tag', default="Unknown", help="Version string (e.g., v2024.01.09)")

    args = parser.parse_args()

    # 2. File Setup
    input_file = args.input
    deck_title = args.deck_name
    
    if args.output:
        output_file = args.output
    else:
        safe_name = "".join([c if c.isalnum() else "_" for c in deck_title])
        output_file = f"{safe_name}.apkg"

    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)

    try:
        df = pd.read_csv(input_file, sep='\t').fillna('')
    except Exception as e:
        print(f"Error reading TSV: {e}")
        sys.exit(1)

    print(f"Loaded {len(df)} rows. Generating deck '{deck_title}' (Version: {args.tag})...")

    # 3. Handle 'Never Miss'
    if 'Never Miss' in df.columns:
        df['Never Miss'] = df['Never Miss'].apply(
            lambda x: str(x).strip() if str(x).strip().startswith('Y') else ''
        )

    # 4. Construct Voice List
    user_voice = args.voice.replace(" ", "_")
    fallbacks = ["Apple_Evan_(Enhanced)", "Microsoft_David", "Microsoft_Zira", "Google_US_English"]
    voice_list_arr = [user_voice] + [v for v in fallbacks if v != user_voice]
    voice_string = ",".join(voice_list_arr)

    # 5. Define Anki Model (Granular)
    # Updated to v3 to include the new 'MoreInfo' field
    model_id = get_stable_id(f"{deck_title}_Granular_TTS_v3")
    
    css = """
        .card { font-family: arial; font-size: 20px; text-align: center; color: black; background-color: white; }
        .label { font-size: 16px; color: #666; margin-bottom: 10px; }
        .answer { margin-top: 20px; }
        .warning { color: red; font-weight: bold; font-size: 16px; border: 2px solid red; padding: 10px; margin-top: 15px; display: inline-block;}
        .more-info { margin-top: 15px; font-size: 16px; }
        .more-info a { color: #007bff; text-decoration: none; font-weight: bold; }
    """

    my_model = genanki.Model(
        model_id,
        f'{deck_title} TTS Model v3',
        fields=[
            {'name': 'Question_Display'}, # 1. HTML for the screen
            {'name': 'Answer_Display'},   # 2. HTML for the screen
            {'name': 'Question_TTS'},     # 3. Plain text full sentence for Audio
            {'name': 'Answer_TTS'},       # 4. Plain text answer for Audio
            {'name': 'NeverMiss'},        # 5. Never Miss Flag
            {'name': 'MoreInfo'},         # 6. More Info URL
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

                    <div style="display:none">{{tts en_US voices=%s:Answer_TTS}}</div>
                ''' % voice_string,
            },
        ],
        css=css
    )

    deck_id = get_stable_id(deck_title)
    my_deck = genanki.Deck(deck_id, deck_title)
    
    # Tag Helper
    def clean_tag(txt):
        return txt.strip().replace(" ", "_").replace("&", "and")
    base_tag = f"TRISH::Blocks::{clean_tag(deck_title)}"

    # --- NEW: Add a "Version/Info" Note ---
    # This creates a special card to track versioning inside Anki
    print(f"Embedding version info: {args.tag}")
    info_guid = genanki.guid_for("DECK_INFO_CARD", deck_title) # Stable ID for this specific card
    
    info_note = genanki.Note(
        model=my_model,
        fields=[
            f"<b>{deck_title}</b><br>Version Information",          # 1. Question_Display
            f"Last Updated: <b>{args.tag}</b><br><br>Check for updates regularly.", # 2. Answer_Display
            "Deck Version Information",                              # 3. Question_TTS
            f"Updated to version {args.tag}",                        # 4. Answer_TTS
            "",                                                      # 5. NeverMiss (Empty)
            ""                                                       # 6. MoreInfo (Empty)
        ],
        tags=[f"TRISH::MetaData"],
        guid=info_guid
    )
    my_deck.add_note(info_note)

    # 6. Generate Notes
    primary_col = df.columns[0] # Condition

    for _, row in df.iterrows():
        condition = str(row[primary_col])
        never_miss = str(row['Never Miss']) if 'Never Miss' in df.columns else ''
        
        # Extract More Info URL (if column exists)
        more_info_url = str(row['More Info']) if 'More Info' in df.columns else ''
        # If it was empty/NaN in pandas, ensure it's an empty string
        if not more_info_url.strip():
            more_info_url = ''

        for col in df.columns:
            # Skip primary key, Never Miss, AND More Info (don't make cards for the link itself)
            if col == primary_col or col == "Never Miss" or col == "More Info":
                continue

            val = str(row[col])
            if not val.strip():
                continue

            # --- Logic for Prompts & Text ---
            
            # 1. Determine the "Prompt" text
            if col == "Salient Signs & Symptoms":
                prompt_html = "What are the <u>Salient Signs & Symptoms</u> of"
                prompt_text = "What are the Salient Signs and Symptoms of"
            elif col == "Diagnostics":
                prompt_html = "How would you <u>Diagnose</u>"
                prompt_text = "How would you Diagnose"
            elif col == "USMLE Classic Presentation":
                prompt_html = "What <u>condition</u> presents as:"
                prompt_text = "What condition presents as"
            else:
                prompt_html = f"What is the <u>{col}</u> of"
                prompt_text = f"What is the {col} of"

            # 2. Prepare Display Fields (HTML Safe)
            val_display = html.escape(val).replace('\n', '<br>')
            cond_display = html.escape(condition)

            # 3. Prepare TTS Fields (Plain Text, Full Sentences)
            val_tts = clean_for_tts(val)
            cond_tts = clean_for_tts(condition)

            tags = [f"{base_tag}", f"TRISH::Conditions::{clean_tag(condition)}"]

            if col == "USMLE Classic Presentation":
                # REVERSED CARD
                # Front: Presentation -> Back: Condition
                
                # Display
                q_disp = f"<div class='label'>{prompt_html}</div><br>{val_display}"
                a_disp = cond_display
                
                # TTS
                q_tts = f"{prompt_text}: {val_tts}"
                a_tts = cond_tts
                
                guid = genanki.guid_for(condition, "Presentation")
                tags.append(f"TRISH::Presentation")

            else:
                # FORWARD CARD
                # Front: Condition -> Back: Detail
                
                # Display
                q_disp = f"<div class='label'>{prompt_html}</div><br>{cond_display}"
                a_disp = val_display

                # TTS
                q_tts = f"{prompt_text} {cond_tts}?"
                a_tts = val_tts

                guid = genanki.guid_for(condition, col)
                tags.append(f"TRISH::{clean_tag(col)}")

            if never_miss:
                tags.append(f"TRISH::Never_Miss")

            # 4. Create Note (Added more_info_url to fields)
            note = genanki.Note(
                model=my_model,
                fields=[
                    q_disp, 
                    a_disp, 
                    q_tts, 
                    a_tts, 
                    never_miss,
                    more_info_url # <--- New Field Data
                ],
                tags=tags,
                guid=guid
            )
            my_deck.add_note(note)

    # 7. Export
    genanki.Package(my_deck).write_to_file(output_file)
    print(f"Voice: {voice_string.split(',')[0]} (plus fallbacks)")
    print(f"Success! Deck saved to: {output_file}")

if __name__ == "__main__":
    main()