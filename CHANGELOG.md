# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.3.2] - 2026-01-12

### Changed
- Upgrade n8n from `2.3.1-amd64` to `2.3.2-amd64`
- Update task runners from `2.3.1` to `2.3.2` with new base image `n8nio/runners:2.3.2-amd64`

### Fixed
- Resolve SSL certificate error in PostgreSQL Docker build
- Create custom PostgreSQL 16 image to replace problematic pgvector compilation
- Update docker-compose.yml to use custom PostgreSQL image with proper environment variables

### Technical
- Replace complex pgvector build process with simplified PostgreSQL 16 configuration
- Ensure all Docker services build successfully without SSL connectivity issues
- Maintain compatibility with existing n8n workflow configurations