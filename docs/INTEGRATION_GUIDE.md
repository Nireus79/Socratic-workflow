# Socratic Workflow - Integration Guide

## Socrates Nexus Integration

Track costs of LLM calls:

```python
from socratic_workflow import CostTracker
from socrates_nexus import LLMClient

tracker = CostTracker()
llm = LLMClient(provider="anthropic", model="claude-opus")
response = llm.chat("query")
tracker.track_call("claude-opus", response.usage.input_tokens, response.usage.output_tokens)
```

## Openclaw Integration

```python
from socratic_workflow.integrations.openclaw import SocraticWorkflowSkill

skill = SocraticWorkflowSkill(use_parallel_executor=True, track_costs=True)
```

## LangChain Integration

```python
from socratic_workflow.integrations.langchain import SocraticWorkflowTool

tool = SocraticWorkflowTool(track_costs=True)
```
