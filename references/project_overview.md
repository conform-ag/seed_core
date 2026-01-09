# Seed Core Project Overview

## Project Description
**Seed Core** is a custom ERPNext application designed to serve as the central management system for a multi-subsidiary seed company. It provides the foundational logic and data structures required to manage seed-specific operations across different territories, including Turkey, Morocco, and Spain.

The application is built on the **Frappe Framework** and is intended to be self-hosted, ensuring data sovereignty and flexibility.

## Goals & Objectives

### 1. Centralized Seed Management
The primary goal is to establish a unified system for managing the core lifecycle of seed production and distribution. This includes:
*   **Variety Management**: Centralized repository for seed varieties and their diverse commercial names.
*   **Crop Definition**: Standardized categorization of crops.
*   **Quality Control**: Integrated lab testing protocols for seed quality assurance.
*   **Processing**: Tracking the processing stages of seed batches.

### 2. Multi-Subsidiary Architecture
The project is designed to support a multi-country structure, ensuring:
*   **Shared Logic**: Common business logic resides in `seed_core` to avoid duplication.
*   **Localization**: Flexibility to extend functionality for specific country requirements (e.g., local compliance in Spain or Morocco) via separate apps or modules while keeping the core clean.
*   **Data Separation**: Controlled access and data isolation between subsidiaries.
*   **Consolidation**: Ability to consolidate invoices, stock levels, and performance goals at the group level.

### 3. Scalable Roll-out
The implementation follows a phased approach:
*   **Phase 1**: Initial roll-out for the parent company (Turkey) and Morocco subsidiary.
*   **Phase 2**: Expansion to Spain and other future territories.

## App Structure & key Modules

The `seed_core` application currently includes the following key modules and Document Types (Doctypes):

*   **Seed Crop**: Defines the types of crops being managed.
*   **Seed Variety**: Manages specific varieties within a crop.
*   **Seed Variety Name**: Handles synonyms and commercial names for varieties.
*   **Seed Segment**: Classifies seeds into specific market or biological segments.
*   **Seed Processing**: Tracks the processing workflows for seed batches.
*   **Lab Test**: Manages quality control and laboratory testing results.

## Technical Stack
*   **Framework**: Frappe (Python/JS)
*   **Base ERP**: ERPNext
*   **Database**: MariaDB (standard Frappe setup)
