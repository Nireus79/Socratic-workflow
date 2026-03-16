# Socratic Workflow - Architecture

## System Overview

Socratic Workflow orchestrates multi-step AI workflows with LLM cost tracking, performance analytics, task dependencies, parallel execution, and error recovery.

## Core Components

### 1. Workflow
Defines sequence of tasks with dependencies.

### 2. Task
Base class for workflow tasks.

### 3. WorkflowEngine
Orchestrates task execution.

### 4. CostTracker
Tracks LLM costs.

### 5. Execution Strategies
Sequential, parallel, and async execution.

## Supported Models (16+)

- Claude Opus-4, Sonnet-3.5, Haiku-4.5
- GPT-4, GPT-4o, GPT-3.5-turbo
- Gemini 1.5 Pro/Flash
- Llama-2-70b, Llama-3-70b
- Mistral-7b, Mistral-Large
