# Socratic Workflow

[![Tests](https://github.com/Nireus79/Socratic-workflow/workflows/Tests/badge.svg)](https://github.com/Nireus79/Socratic-workflow/actions)
[![Code Quality](https://github.com/Nireus79/Socratic-workflow/workflows/Quality/badge.svg)](https://github.com/Nireus79/Socratic-workflow/actions)
[![PyPI](https://img.shields.io/pypi/v/socratic-workflow)](https://pypi.org/project/socratic-workflow/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Why Socratic Workflow?

Building multi-step AI workflows is complex. Socratic Workflow handles the production challenges:

- **Cost Tracking** - Track LLM costs across 16+ models and 5 providers (Claude, GPT-4, Gemini, Llama, Mistral)
- **Dependency Management** - Define complex task graphs with automatic dependency resolution
- **Parallel Execution** - Run independent tasks concurrently for maximum performance
- **Error Recovery** - Automatic retry logic with exponential backoff and graceful degradation
- **Performance Analytics** - Measure execution time, bottlenecks, and success rates in real-time

Production-grade workflow orchestration system with **LLM cost tracking**, **performance analytics**, and **dependency management**.

## Features

- **🔄 Workflow Orchestration** - Define and execute multi-step AI workflows
- **💰 Cost Tracking** - Track LLM costs across providers (Claude, GPT-4, Gemini, etc.)
- **📊 Performance Analytics** - Measure execution time, success rates, bottlenecks
- **🔗 Task Dependencies** - Manage complex task graphs with dependencies
- **⚡ Parallel Execution** - Run independent tasks concurrently for speed
- **💾 State Management** - Save/restore workflow state for resilience
- **🔄 Error Recovery** - Retry logic and graceful degradation
- **🔌 Framework Integration** - Works with Openclaw, LangChain, Socratic Agents

## Quick Start

### Installation

```bash
# Basic installation
pip install socratic-workflow

# With LangChain integration
pip install socratic-workflow[langchain]

# With Openclaw integration
pip install socratic-workflow[openclaw]

# With everything
pip install socratic-workflow[all]
```

### Simple Workflow

```python
from socratic_workflow import Workflow, Task, WorkflowEngine

# Define a custom task
class GreetingTask(Task):
    def execute(self, context):
        name = self.config.get("name", "World")
        return {"greeting": f"Hello, {name}!"}

# Build workflow
workflow = Workflow("Greeting Pipeline")
workflow.add_task("greet", GreetingTask(name="Alice"))

# Execute
engine = WorkflowEngine()
result = engine.execute(workflow)

print(result.success)  # True
print(result.task_results)  # {"greet": {"greeting": "Hello, Alice!"}}
print(f"Execution time: {result.duration:.2f}s")
```

### Workflow with Dependencies

```python
from socratic_workflow import Workflow, SimpleTask, WorkflowEngine

# Create workflow with dependencies
workflow = Workflow("Multi-Step Pipeline")
workflow.add_task("step1", SimpleTask(result={"data": "processed"}))
workflow.add_task("step2", SimpleTask(result={"analysis": "complete"}), depends_on=["step1"])
workflow.add_task("step3", SimpleTask(result={"summary": "done"}), depends_on=["step2"])

# Execute
engine = WorkflowEngine()
result = engine.execute(workflow)

print(result.success)
print(result.duration)
```

### Async Execution

```python
import asyncio
from socratic_workflow import Workflow, SimpleTask, WorkflowEngine

async def main():
    workflow = Workflow("Async Pipeline")
    workflow.add_task("task1", SimpleTask(result={"value": 1}))
    workflow.add_task("task2", SimpleTask(result={"value": 2}))

    engine = WorkflowEngine()
    result = await engine.execute_async(workflow)

    print(f"Success: {result.success}")
    print(f"Duration: {result.duration:.2f}s")

asyncio.run(main())
```

## Core Concepts

### Workflow

A workflow defines a sequence of tasks with their dependencies. Use the builder pattern to create workflows:

```python
workflow = Workflow("My Pipeline", description="Optional description")
workflow.add_task("task1", MyTask())
workflow.add_task("task2", MyTask(), depends_on=["task1"])
workflow.add_task("task3", MyTask(), depends_on=["task1"])  # Parallel with task2
```

### Tasks

Create custom tasks by inheriting from `Task`:

```python
from socratic_workflow import Task

class CustomTask(Task):
    def execute(self, context):
        # context contains results from previous tasks
        return {"result": "value"}

    async def execute_async(self, context):
        # Optional: override for true async execution
        return await self.execute(context)
```

### WorkflowEngine

The engine orchestrates task execution:

```python
engine = WorkflowEngine()

# Sync execution
result = engine.execute(workflow)

# Async execution
result = await engine.execute_async(workflow)

# Save/load state
engine.save_state("workflow.json")
engine.load_state("workflow.json")
```

### Results

Get detailed execution results:

```python
result = engine.execute(workflow)

print(result.success)          # bool
print(result.duration)         # float (seconds)
print(result.task_results)     # Dict[str, Any]
print(result.errors)           # Dict[str, str]
print(result.to_dict())        # Full result as dict
```

## API Reference

### Workflow

```python
class Workflow:
    def __init__(self, name: str, description: str = "")
    def add_task(self, task_id: str, task: Task, depends_on: Optional[List[str]] = None) -> Workflow
    def get_task(self, task_id: str) -> Optional[Task]
    def list_tasks(self) -> List[str]
    def get_dependencies(self, task_id: str) -> List[str]
    def to_dict(self) -> Dict[str, Any]
```

### Task

```python
class Task(ABC):
    def __init__(self, name: Optional[str] = None, **kwargs)
    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]
    async def execute_async(self, context: Dict[str, Any]) -> Dict[str, Any]
    def to_dict(self) -> Dict[str, Any]
```

### WorkflowEngine

```python
class WorkflowEngine:
    def __init__(self, llm_client: Optional[Any] = None)
    def execute(self, workflow: Workflow) -> WorkflowResult
    async def execute_async(self, workflow: Workflow) -> WorkflowResult
    def save_state(self, path: str) -> None
    def load_state(self, path: str) -> None
```

### WorkflowResult

```python
class WorkflowResult:
    success: bool
    duration: float
    task_results: Dict[str, Any]
    errors: Dict[str, str]
    metrics: Dict[str, Any]
    def to_dict(self) -> Dict[str, Any]
```

## Examples

### Example 1: Basic Workflow

See `examples/01_basic_workflow.py` for a complete example.

### Example 2: Cost Tracking

See `examples/02_cost_tracking.py` (Phase 2).

### Example 3: Parallel Execution

See `examples/03_parallel_execution.py` (Phase 3).

### Example 4: Error Recovery

See `examples/04_error_recovery.py` (Phase 3).

## Advanced Features

### Cost Tracking

Track LLM costs across multiple providers:

```python
from socratic_workflow import CostTracker

tracker = CostTracker()

# Track individual calls
cost1 = tracker.track_call("claude-opus-4", 1000, 500)
cost2 = tracker.track_call("gpt-4", 1000, 500)

# Get summary
summary = tracker.get_summary()
print(f"Total cost: ${summary['total_cost_usd']:.4f}")
print(f"By provider: {summary['cost_by_provider']}")

# Get recommendations
recommendations = tracker.get_recommendations()
for rec in recommendations:
    print(f"- {rec}")
```

Supports 16+ models across 5 providers:
- **Anthropic**: Claude Opus-4, Sonnet-3.5, Haiku-4.5
- **OpenAI**: GPT-4, GPT-4o, GPT-3.5-turbo
- **Google**: Gemini 1.5 Pro, Gemini 1.5 Flash
- **Meta**: Llama-2-70b, Llama-3-70b
- **Mistral**: Mistral-7b, Mistral-Large

### Parallel Execution

Run independent tasks concurrently:

```python
from socratic_workflow.execution.executor import ParallelExecutor

executor = ParallelExecutor(max_workers=5)
result = await executor.execute_parallel(workflow)

metrics = executor.get_execution_metrics()
print(f"Success rate: {metrics['success_rate']:.1%}")
```

### Error Recovery

Automatic retry with exponential backoff:

```python
from socratic_workflow.execution.retry import RetryConfig, retry

config = RetryConfig(
    max_attempts=3,
    initial_delay=1.0,
    exponential_base=2.0,
    jitter=True
)

@retry(config)
def risky_operation():
    # Automatically retried on failure
    return result
```

### Performance Metrics

Collect and analyze performance data:

```python
from socratic_workflow.analytics import MetricsCollector

collector = MetricsCollector()
# ... execute workflow ...
summary = collector.get_summary()

print(f"Total duration: {summary['total_duration']:.2f}s")
print(f"Bottlenecks: {summary['bottlenecks']}")
print(f"Success rate: {summary['success_rate']:.1%}")
```

## Integrations

### LangChain

Integrate with LangChain agents:

```python
import json
from socratic_workflow.integrations.langchain import SocraticWorkflowTool
from langchain.agents import Tool

tool = SocraticWorkflowTool(track_costs=True)

# Create LangChain tool
langchain_tool = Tool(
    name="execute_workflow",
    func=tool.execute_sync,
    description=tool.get_tool_description()
)

# Use in agent
from langchain.agents import initialize_agent
agent = initialize_agent([langchain_tool], llm, agent="zero-shot-react-description")
```

### Openclaw

Create Openclaw skills:

```python
from socratic_workflow.integrations.openclaw import SocraticWorkflowSkill

skill = SocraticWorkflowSkill(
    use_parallel_executor=True,
    track_costs=True,
    track_metrics=True
)

# Get capabilities for discovery
capabilities = skill.get_capabilities()

# Execute workflow
result = await skill.execute_workflow({
    "name": "My Workflow",
    "tasks": [
        {"id": "task1", "type": "SimpleTask", "result": {"status": "ok"}}
    ]
})
```

## Roadmap

### Phase 1: Core Infrastructure ✅
- [x] Workflow definition and execution
- [x] Task base class
- [x] State management
- [x] Sync and async execution

### Phase 2: Cost Tracking & Analytics ✅
- [x] Cost tracker with provider pricing (16+ models)
- [x] Performance metrics collection
- [x] Cost recommendations

### Phase 3: Advanced Execution ✅
- [x] Parallel task execution with asyncio
- [x] Task scheduler with dependency resolution
- [x] Retry logic with exponential backoff

### Phase 4: Integrations ✅
- [x] Openclaw skill integration
- [x] LangChain tool integration
- [x] Socratic Agents compatibility

### Phase 5: Polish & Release ✅
- [x] Comprehensive documentation
- [x] 4 complete examples
- [x] PyPI publication ready
- [x] 95% test coverage (188 tests)
- [x] All quality checks passing

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=src/socratic_workflow

# Specific test file
pytest tests/unit/test_engine.py -v
```

## Quality

```bash
# Format code
black src/ tests/ examples/

# Lint
ruff check src/ tests/ examples/

# Type check
mypy src/socratic_workflow
```

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Project Status

**Version**: 0.1.0 (MVP) ✅

### Statistics
- **Lines of Code**: ~3,400
- **Test Coverage**: 95% (188 tests)
- **Supported Python**: 3.9, 3.10, 3.11, 3.12
- **Quality**: Black, Ruff, MyPy ✅
- **CI/CD**: GitHub Actions (automated testing and quality checks)

### Implementation Progress
- ✅ Phase 1: Core Infrastructure (100%)
- ✅ Phase 2: Cost Tracking & Analytics (100%)
- ✅ Phase 3: Advanced Execution (100%)
- ✅ Phase 4: Integrations (100%)
- ✅ Phase 5: Polish & Release (100%)

## Support

- 📖 [Documentation](https://github.com/Nireus79/Socratic-workflow#readme)
- 🐛 [Issues](https://github.com/Nireus79/Socratic-workflow/issues)
- 💬 [Discussions](https://github.com/Nireus79/Socratic-workflow/discussions)

## Related Projects

- [Socratic Agents](https://github.com/Nireus79/Socratic-agents) - Multi-agent orchestration
- [Socratic RAG](https://github.com/Nireus79/Socratic-rag) - Retrieval-augmented generation
- [Socratic Analyzer](https://github.com/Nireus79/Socratic-analyzer) - Code analysis
- [Socrates Nexus](https://github.com/Nireus79/socrates-nexus) - Universal LLM client

---

**Built with ❤️ by the Socratic Ecosystem**
