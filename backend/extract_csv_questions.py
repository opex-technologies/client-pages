#!/usr/bin/env python3
"""
Extract questions from questions.csv for network survey form generation.
"""

import pandas as pd
import json
import sys
import os

def determine_input_type(question, data_type=None):
    """
    Determine the appropriate input type based on question content.
    
    Args:
        question (str): The question text
        data_type (str): The data type from column C (if available)
        
    Returns:
        str: Input type (radio, number, text, textarea)
    """
    question_lower = question.lower()
    
    # Boolean/Yes-No questions - use radio buttons
    if any(keyword in question_lower for keyword in [
        'do you', 'can you', 'will you', 'are you', 'is your', 'does your',
        'support', 'offer', 'provide', 'include', 'handle'
    ]):
        # Check if it's asking for details or explanations
        if any(detail in question_lower for detail in [
            'describe', 'explain', 'detail', 'how do you', 'what is your',
            'list', 'what are your'
        ]):
            return 'textarea'
        else:
            return 'radio'
    
    # Number questions
    if any(keyword in question_lower for keyword in [
        'how many', 'number of', 'maximum', 'minimum', 'year'
    ]):
        return 'number'
    
    # Text area for descriptive questions
    if any(keyword in question_lower for keyword in [
        'describe', 'explain', 'detail', 'list', 'what', 'how', 'where'
    ]):
        return 'textarea'
    
    # Default to text input for short answers
    return 'text'

def extract_questions_from_csv(csv_file_path):
    """
    Extract questions from the CSV scorecard file.
    
    Args:
        csv_file_path (str): Path to the CSV file
        
    Returns:
        dict: Dictionary containing processed questions data
    """
    try:
        # Read the CSV file with proper encoding
        df = pd.read_csv(csv_file_path, encoding='utf-8')
        
        print(f"CSV shape: {df.shape}")
        print(f"Column names: {list(df.columns)}")
        
        # The first column should contain questions
        question_column = df.columns[0]
        response_column = df.columns[2] if len(df.columns) > 2 else None
        
        print(f"Using question column: '{question_column}'")
        if response_column:
            print(f"Using response column: '{response_column}'")
        
        # Extract questions, skipping header rows and empty/non-question rows
        questions_data = []
        
        for index, row in df.iterrows():
            question = str(row[question_column]).strip()
            response_type = str(row[response_column]).strip() if response_column else ""
            
            # Skip empty rows, headers, or non-question rows
            if (question == 'nan' or 
                question == '' or 
                'scorecard' in question.lower() or
                'company information' in question.lower() or
                'management' in question.lower() or
                'sd wan requirements' in question.lower() or
                'cloud firewall' in question.lower() or
                'remote access' in question.lower() or
                'totals' in question.lower() or
                'scoring' in question.lower() or
                question.endswith('%') or
                question.startswith('#') or
                len(question) < 10):  # Skip very short entries
                continue
            
            # Determine input type
            input_type = determine_input_type(question, response_type)
            
            # Create question data
            question_data = {
                "question": question,
                "data_type": response_type if response_type != 'nan' else "General",
                "input_type": input_type,
                "field_id": f"field_{len(questions_data) + 1}"
            }
            
            questions_data.append(question_data)
            
            # Stop at a reasonable number for the form
            if len(questions_data) >= 50:
                break
        
        print(f"Extracted {len(questions_data)} questions")
        
        # Show sample questions
        print("\nSample questions:")
        for i, q in enumerate(questions_data[:5]):
            print(f"{i+1}. {q['question'][:80]}...")
            print(f"   Type: {q['input_type']} | Category: {q['data_type']}")
            print()
        
        return {
            "questions": questions_data,
            "total_count": len(questions_data)
        }
        
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return None

def main():
    """Main function to extract and process CSV questions."""
    csv_path = "/Users/landoncolvig/Documents/opex-technologies/questions.csv"
    
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        sys.exit(1)
    
    print("Extracting questions from CSV...")
    data = extract_questions_from_csv(csv_path)
    
    if data:
        print(f"Successfully extracted {data['total_count']} questions")
        
        # Save to JSON file for use in HTML generation
        output_path = "/Users/landoncolvig/Documents/opex-technologies/backend/csv_questions_data.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Data saved to: {output_path}")
        return data
    else:
        print("Failed to extract data")
        sys.exit(1)

if __name__ == "__main__":
    main()