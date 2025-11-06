#!/bin/bash
#
# Backup Question Database CSV
# Creates timestamped backups of the Question Database CSV file
#
# Usage: ./backup_question_database.sh
#
# Created: November 5, 2025

# Configuration
PROJECT_ROOT="/Users/landoncolvig/Documents/opex-technologies"
CSV_FILE="Question Database(Sheet1).csv"
BACKUP_DIR="$PROJECT_ROOT/Q4 form scoring project/database/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="question_database_backup_${TIMESTAMP}.csv"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}Question Database Backup Script${NC}"
echo "================================"
echo ""

# Check if CSV exists
if [ ! -f "$PROJECT_ROOT/$CSV_FILE" ]; then
    echo -e "${RED}Error: CSV file not found at $PROJECT_ROOT/$CSV_FILE${NC}"
    exit 1
fi

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Copy CSV with timestamp
cp "$PROJECT_ROOT/$CSV_FILE" "$BACKUP_DIR/$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Backup created successfully${NC}"
    echo "  Location: $BACKUP_DIR/$BACKUP_FILE"

    # Get file size
    FILE_SIZE=$(ls -lh "$BACKUP_DIR/$BACKUP_FILE" | awk '{print $5}')
    echo "  Size: $FILE_SIZE"

    # Count rows
    ROW_COUNT=$(wc -l < "$BACKUP_DIR/$BACKUP_FILE")
    echo "  Rows: $ROW_COUNT"

    # Clean up old backups (keep last 10)
    echo ""
    echo "Cleaning up old backups (keeping last 10)..."
    cd "$BACKUP_DIR"
    ls -t question_database_backup_*.csv | tail -n +11 | xargs -I {} rm -f {}

    BACKUP_COUNT=$(ls -1 question_database_backup_*.csv 2>/dev/null | wc -l)
    echo -e "${GREEN}✓ Total backups: $BACKUP_COUNT${NC}"

else
    echo -e "${RED}✗ Backup failed${NC}"
    exit 1
fi
