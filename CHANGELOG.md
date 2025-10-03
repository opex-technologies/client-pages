# Changelog

All notable changes to the Opex Technologies repository will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Complete survey system with 14 specialized assessment forms organized by opportunity type/subtype
- Comprehensive question database integration from CSV source with 1,500+ total questions
- Dynamic form generation with intelligent input type detection (radio, textarea, number, text)
- Survey forms directory structure (`Web/surveys/`) for better organization
- Individual survey forms covering:
  - Managed Service Provider capabilities (208 questions)
  - Cloud Disaster Recovery as a Service (123 questions)
  - Contact Center as a Service (105 questions)
  - Intelligent Virtual Assistant (63 questions)
  - Data Center Colocation (96 questions)
  - Unified Communications as a Service (98 questions)
  - Security Managed Detection & Response (42 questions)
  - Security Penetration Testing (14 questions)
  - Network Aggregation (38 questions)
  - Network as a Service (83 questions)
  - Network SD-WAN (106 questions)
  - Security SASE (67 questions)
  - Expense Management Mobile (106 questions)
- Automated question categorization and input type mapping from CSV data weights
- Universal "All/All" questions automatically included across all relevant survey types
- Enhanced documentation with comprehensive survey system overview
- Initial repository documentation with CLAUDE.md file
- CHANGELOG.md for tracking project changes
- Repository information section with GitHub URL

### Changed
- Renamed `networksurvey.html` to `network-sase-survey.html` for consistency
- Updated CLAUDE.md to include comprehensive survey system documentation
- Improved form submission data routing with unique identifiers per survey type
- Enhanced BigQuery integration to support multiple specialized survey data tables

## Previous Changes

### Existing Features
- Contact form (`Web/initialwebpage.html`) with Opex Technologies branding
- SASE Network Security Survey form (`Web/networksurvey.html`) with dynamic question generation
- Google Cloud Function webhook endpoint (`backend/main.py`) for processing form submissions
- BigQuery integration with dynamic table creation and schema evolution
- SASE RFI data backloading scripts (`backload-data/`) for historical data integration
- Static asset hosting for Opex Technologies logo
- Responsive design and error handling across all forms
- Comprehensive data validation and retry logic in backend processing

### Infrastructure
- Google Cloud Function deployment for webhook processing
- BigQuery dataset (`opex_dev`) with dynamic table management
- Google Cloud Storage for static assets
- Historical data integration from SASE RFI CSV files