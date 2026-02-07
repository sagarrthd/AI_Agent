from __future__ import annotations

from typing import List, Dict


import re

def parse_table_response(text: str) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    print(f"Parsing AI Response ({len(text)} chars)...")
    
    # Extract only the table part
    # Look for lines starting with | (ignoring whitespace)
    # This regex finds lines starting with a pipe
    table_lines = re.findall(r"^\s*\|.*", text, re.MULTILINE)
    
    if not table_lines:
        print("⚠ No Markdown table found in response.")
        return []
        
    print(f"Found {len(table_lines)} potential table rows.")
    
    for line in table_lines:
        line = line.strip()
        if not line or "|" not in line:
            continue
            
        # Skip header and separator lines
        if "Test ID" in line or "---" in line or "test_id" in line.lower():
            continue
            
        # Split by pipe
        parts = [p.strip() for p in line.split("|")]
        
        # Remove empty strings caused by leading/trailing pipes
        # e.g. "| A | B |" -> ["", "A", "B", ""]
        clean_parts = [p for p in parts if p]
        
        if len(clean_parts) < 6:
            # Maybe fewer columns? Try to map what we have
            continue
            
        # Assuming strict order from prompt:
        # Test ID | Title | Preconditions | Steps | Expected Results | Requirement IDs
        
        try:
            row = {
                "test_id": clean_parts[0],
                "title": clean_parts[1],
                "preconditions": clean_parts[2],
                # Steps might contain newlines or be truncated. 
                # In standard markdown table, newlines are usually <br> or just single line.
                "steps": clean_parts[3],
                "expected": clean_parts[4],
                "requirements": clean_parts[5] if len(clean_parts) > 5 else ""
            }
            rows.append(row)
        except IndexError:
            continue
            
    print(f"✓ Parsed {len(rows)} test cases from AI response.")
    return rows
