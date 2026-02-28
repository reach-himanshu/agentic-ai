# Azure OpenAI Integration Plan

This document outlines the implementation plan for integrating Azure OpenAI into the orchestrator layer using the AutoGen framework.

## Overview
The goal is to move from keyword-based intent extraction to a dynamic, LLM-driven orchestration using AutoGen's multi-agent system, specifically tailored for Azure OpenAI.

## Proposed Changes

### 1. Orchestrator Dependencies
- **File**: `orchestrator/pyproject.toml`
- **Addition**: `autogen-agentchat`, `python-dotenv`
- **Purpose**: To provide the AutoGen framework and environment variable support.

### 2. Configuration Management
- **File**: `orchestrator/config.py`
- **Features**: 
    - Support for `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, `AZURE_OPENAI_API_VERSION`, and `AZURE_OPENAI_MODEL_NAME`.
    - `get_llm_config()` helper for AutoGen-compatible configuration lists.
- **File**: `orchestrator/.env`
- **Purpose**: Secure storage of API credentials.

### 3. Agent Implementation
- **Executor Agent** (`orchestrator/agents/executor.py`):
    - Refactored to properly bind MCP tools using AutoGen's `FunctionTool`.
- **Planner Agent** (`orchestrator/agents/planner.py`):
    - Refactored to use `AssistantAgent` and `UserProxyAgent`.
    - Implements dynamic tool registration and LLM-driven chat initiation.
    - Maintains Human-in-the-Loop (HITL) points for sensitive operations like CRM stage updates.

## Verification Plan

### 1. Connectivity Test
- **Script**: `orchestrator/test_llm.py`
- **Method**: Run `.\.venv\Scripts\python test_llm.py` to verify the LLM can respond to basic queries.

### 2. End-to-End Test
- **Method**: Start the backend, orchestrator, and frontend.
- **Interaction**: Send "Find Acme Corp" and "Update Acme to qualified" in the UI.
- **Expected**: The agent extracts parameters using the LLM and triggers the ConfirmationCard for updates.

## Current Status
- [x] Dependency Installation (Virtual Env)
- [x] Configuration Setup
- [x] Agent Refactoring
- [x] Basic Connectivity Verification
