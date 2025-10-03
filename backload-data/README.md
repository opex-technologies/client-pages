# SASE RFI Data Backload

This directory contains scripts for backloading the SASE RFI scorecard data from CSV to BigQuery.

## Overview

The backload process transforms the historical SASE RFI vendor responses into the same format used by the network security survey web form, enabling comprehensive analysis alongside new survey data.

## Files

- `backload_sase_rfi.py` - Main backload script
- `verify_data.py` - Data integrity verification script
- `SASE RFI.csv` - Source CSV file with vendor responses
- `requirements.txt` - Python dependencies
- `README.md` - This documentation

## Data Processing

### Source Data
- **Input**: `SASE RFI.csv` containing 11 vendor responses across 44+ evaluation criteria
- **Vendors**: CBTS, Commandlink, Cato Networks, RapidScale, Lumen, Nitel, New Horizon Communications, Spectrotel, Windstream, AT&T Enterprises
- **Categories**: Company Information, Circuit Management, SD-WAN Features, Cloud Firewall, Remote Access, etc.

### Target Schema
- **Dataset**: `opex_dev`
- **Table**: `network_security_survey`
- **Format**: Compatible with existing web form submissions
- **Field Names**: Question text sanitized to lowercase with underscores (e.g., "Company Name" → "company_name")

### Transformation Logic
1. **Question Mapping**: CSV questions mapped to survey form fields using exact text matching
2. **Response Normalization**: Vendor responses converted to standard format:
   - Radio fields: "yes", "no", or "partial"
   - Text/Textarea fields: Original response preserved
   - Number fields: Numeric values extracted
3. **Metadata Addition**: Added `source: "sase-rfi-backload"`, `timestamp`, and contact fields

## Usage

### Prerequisites
```bash
pip install -r requirements.txt
```

### Running the Backload
```bash
python3 backload_sase_rfi.py
```

### Verifying Data Integrity
```bash
python3 verify_data.py
```

## Results

✅ **Successfully backloaded 11 vendor records** to `opex-data-lake-k23k4y98m.opex_dev.network_security_survey`

### Vendor Records Inserted:
- AT&T Enterprises, LLC
- CBTS (2 records - appears twice in CSV)
- Cato Networks  
- Commandlink
- Lumen
- New Horizon Communications
- Nitel
- RapidScale
- Spectrotel
- Windstream

### Sample Data Verification:
- All company names, founding years, and headquarters properly mapped
- Circuit procurement responses correctly normalized (yes/no/partial)
- Mid-session traffic shifting capabilities captured
- Content filtering features documented
- Complex vendor responses (like Cato's detailed founding story) preserved

### Field Coverage:
- 100% coverage for core company information fields
- All survey questions successfully mapped from CSV to database schema
- Response normalization working correctly for radio, text, and numeric fields

## Integration

The backloaded data is now available in the same table as web form submissions, enabling:
- **Unified Analytics**: Historical and new vendor data in single queries
- **Trend Analysis**: Compare vendor capabilities over time
- **Comprehensive Reporting**: Full vendor landscape analysis
- **Data Consistency**: Same field names and formats as live survey data

## Technical Notes

- Uses the same BigQuery client and table creation logic as the existing Cloud Function
- Maintains compatibility with existing analytics workflows
- Includes comprehensive error handling and validation
- Source tracking via `source` field distinguishes backloaded from web form data
- All timestamps preserved for audit trail