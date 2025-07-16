#!/usr/bin/env python3
"""
Extract questions and data types from Excel file for network survey form generation.
"""

import pandas as pd
import json
import sys
import os

def extract_sase_rfi_data(excel_file_path):
    """
    Extract questions from column A and data types from column C of SASE RFI tab.
    
    Args:
        excel_file_path (str): Path to the Excel file
        
    Returns:
        dict: Dictionary containing questions and data_types lists
    """
    try:
        # First, let's check what sheets are available
        xl_file = pd.ExcelFile(excel_file_path)
        print(f"Available sheets: {xl_file.sheet_names}")
        
        # Look for SASE RFI sheet (case insensitive)
        target_sheet = None
        for sheet in xl_file.sheet_names:
            if 'sase' in sheet.lower() and 'rfi' in sheet.lower():
                target_sheet = sheet
                break
        
        if not target_sheet:
            print("SASE RFI sheet not found. Using first sheet as fallback.")
            target_sheet = xl_file.sheet_names[0]
        
        print(f"Using sheet: {target_sheet}")
        
        # First read the sheet to see its structure
        df = pd.read_excel(excel_file_path, sheet_name=target_sheet)
        print(f"Sheet shape: {df.shape}")
        print(f"Column names: {list(df.columns)}")
        
        # Search for SASE-related questions
        sase_mask = df['Question'].str.contains('SASE|sase|Secure Access|Zero Trust|SSE|ZTNA', case=False, na=False)
        sase_questions = df[sase_mask]
        
        print(f"Found {len(sase_questions)} SASE-related questions")
        if len(sase_questions) > 0:
            print("SASE questions preview:")
            for i, row in sase_questions.head(10).iterrows():
                print(f"  {i}: {row['Question'][:100]}...")
        
        # Extract questions from the Question column and data types from Category column
        if len(sase_questions) > 0:
            # Use SASE-specific questions
            questions = sase_questions['Question'].dropna().tolist()
            data_types = sase_questions['Category'].dropna().tolist()
            print(f"Using {len(questions)} SASE-specific questions")
        else:
            # If no SASE questions found, let's look for network/security related questions
            network_mask = df['Question'].str.contains('network|security|firewall|VPN|endpoint|access|authentication', case=False, na=False)
            network_questions = df[network_mask]
            
            if len(network_questions) > 0:
                questions = network_questions['Question'].dropna().tolist()
                data_types = network_questions['Category'].dropna().tolist()
                print(f"Using {len(questions)} network/security-related questions")
            else:
                # Fallback to all questions
                questions = df['Question'].dropna().tolist()
                data_types = df['Category'].dropna().tolist()
                print(f"Using all {len(questions)} questions as fallback")
        
        # Clean up the data - remove any empty strings
        questions = [str(q).strip() for q in questions if str(q).strip() and str(q) != 'nan']
        data_types = [str(dt).strip() for dt in data_types if str(dt).strip() and str(dt) != 'nan']
        
        # Create combined data structure
        combined_data = []
        max_length = max(len(questions), len(data_types))
        
        for i in range(max_length):
            question = questions[i] if i < len(questions) else ""
            data_type = data_types[i] if i < len(data_types) else "text"
            
            if question:  # Only include entries with actual questions
                combined_data.append({
                    "question": question,
                    "data_type": data_type,
                    "field_id": f"field_{i+1}"
                })
        
        return {
            "questions": questions,
            "data_types": data_types,
            "combined": combined_data
        }
        
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return None

def main():
    """Main function to extract and display Excel data."""
    excel_path = "/Users/landoncolvig/Documents/opex-technologies/Question Database.xlsx"
    
    if not os.path.exists(excel_path):
        print(f"Error: Excel file not found at {excel_path}")
        sys.exit(1)
    
    print("Extracting data from SASE RFI tab...")
    data = extract_sase_rfi_data(excel_path)
    
    if data:
        print(f"Successfully extracted {len(data['combined'])} question/data type pairs")
        print("\nSample data:")
        for i, item in enumerate(data['combined'][:5]):  # Show first 5 items
            print(f"{i+1}. Question: {item['question'][:100]}...")
            print(f"   Data Type: {item['data_type']}")
            print()
        
        # Save to JSON file for use in HTML generation
        output_path = "/Users/landoncolvig/Documents/opex-technologies/backend/sase_rfi_data.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Data saved to: {output_path}")
        return data
    else:
        print("Failed to extract data")
        sys.exit(1)

if __name__ == "__main__":
    main()