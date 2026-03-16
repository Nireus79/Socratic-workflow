# Socratic Workflow - API Reference

## Workflow

```python
class Workflow:
    def __init__(self, name: str, description: str = "")
    def add_task(self, task_id: str, task: Task, depends_on: Optional[List[str]] = None) -> Workflow
    def get_task(self, task_id: str) -> Optional[Task]
    def list_tasks(self) -> List[str]
    def get_dependencies(self, task_id: str) -> List[str]
```

## Task

```python
class Task(ABC):
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]
    async def execute_async(self, context: Dict[str, Any]) -> Dict[str, Any]
```

## WorkflowEngine

```python
class WorkflowEngine:
    def execute(self, workflow: Workflow) -> WorkflowResult
    async def execute_async(self, workflow: Workflow) -> WorkflowResult
    def save_state(self, path: str) -> None
    def load_state(self, path: str) -> None
```

## WorkflowResult

```python
class WorkflowResult:
    success: bool
    duration: float
    task_results: Dict[str, Any]
    errors: Dict[str, str]
    metrics: Dict[str, Any]
```

## CostTracker

```python
class CostTracker:
    def track_call(self, model: str, input_tokens: int, output_tokens: int) -> float
    def get_summary(self) -> Dict
    def get_recommendations(self) -> List[str]
```
