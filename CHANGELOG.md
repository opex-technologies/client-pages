# Changelog

All notable changes to the Opex Technologies repository will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial repository documentation with CLAUDE.md file
- CHANGELOG.md for tracking project changes
- Repository information section with GitHub URL

### Changed
- Updated CLAUDE.md to include GitHub repository reference

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