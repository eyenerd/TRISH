#!/usr/bin/env python3
import sys
import argparse
import ezodf

def export_sheet_to_tsv(ods_file, sheet_name, output_file=None):
    """
    Export a specific sheet from an .ods file to TSV format.
    
    :param ods_file: Path to the .ods file
    :param sheet_name: Name of the sheet to export
    :param output_file: Optional output file path (defaults to sheet_name.tsv if not specified)
    """
    try:
        # Open the .ods document
        doc = ezodf.opendoc(ods_file)
        
        # Find the specified sheet
        target_sheet = None
        for sheet in doc.sheets:
            if sheet.name == sheet_name:
                target_sheet = sheet
                break
        
        # Raise an error if sheet not found
        if target_sheet is None:
            raise ValueError(f"Sheet '{sheet_name}' not found in the workbook")
        
        # Determine output filename
        if output_file is None:
            output_file = f"{sheet_name}.tsv"
        
        # Write to TSV
        with open(output_file, 'w', encoding='utf-8') as tsv_file:
            for row in target_sheet.rows():
                # Convert row to tab-separated string, handling None values
                row_data = [str(cell.value) if cell.value is not None else '' for cell in row]
                tsv_line = '\t'.join(row_data)
                tsv_file.write(tsv_line + '\n')
        
        print(f"Successfully exported sheet '{sheet_name}' to {output_file}")
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def main():
    # Set up argument parsing
    parser = argparse.ArgumentParser(description='Export an .ods sheet to TSV')
    parser.add_argument('file', help='Path to the .ods file')
    parser.add_argument('sheet', help='Name of the sheet to export')
    parser.add_argument('-o', '--output', help='Optional output TSV file path', default=None)
    
    # Parse arguments
    args = parser.parse_args()
    
    # Call export function
    export_sheet_to_tsv(args.file, args.sheet, args.output)

if __name__ == '__main__':
    main()
