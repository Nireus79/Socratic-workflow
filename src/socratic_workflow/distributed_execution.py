"""Distributed execution support for socratic-workflow."""
import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from uuid import uuid4

logger = logging.getLogger(__name__)


class TaskState(Enum):
    """Task execution states."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TaskResult:
    """Result of task execution."""
    task_id: str
    status: TaskState
    output: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_ms: float = 0.0


@dataclass
class DistributedTask:
    """Represents a task for distributed execution."""
    task_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    function: Optional[Callable] = None
    args: List[Any] = field(default_factory=list)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    status: TaskState = TaskState.PENDING
    max_retries: int = 3
    timeout_seconds: int = 300
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.now)


class TaskQueue:
    """In-memory task queue for distributed execution."""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.pending_tasks: List[DistributedTask] = []
        self.active_tasks: Dict[str, DistributedTask] = {}
        self.completed_tasks: Dict[str, TaskResult] = {}
        self.lock = asyncio.Lock()
    
    async def enqueue(self, task: DistributedTask) -> str:
        """Enqueue a task for execution."""
        async with self.lock:
            task.status = TaskState.QUEUED
            self.pending_tasks.append(task)
            self.pending_tasks.sort(key=lambda t: t.priority, reverse=True)
        return task.task_id
    
    async def dequeue(self) -> Optional[DistributedTask]:
        """Dequeue next pending task."""
        async with self.lock:
            if self.pending_tasks and len(self.active_tasks) < self.max_workers:
                task = self.pending_tasks.pop(0)
                task.status = TaskState.RUNNING
                self.active_tasks[task.task_id] = task
                return task
        return None
    
    async def mark_completed(self, task_id: str, result: TaskResult) -> None:
        """Mark task as completed."""
        async with self.lock:
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
            self.completed_tasks[task_id] = result
    
    async def get_status(self, task_id: str) -> Optional[TaskState]:
        """Get task status."""
        async with self.lock:
            if task_id in self.completed_tasks:
                return self.completed_tasks[task_id].status
            if task_id in self.active_tasks:
                return self.active_tasks[task_id].status
            for task in self.pending_tasks:
                if task.task_id == task_id:
                    return task.status
        return None
    
    async def get_result(self, task_id: str) -> Optional[TaskResult]:
        """Get task result."""
        async with self.lock:
            return self.completed_tasks.get(task_id)


class DistributedExecutor:
    """Executes tasks from a distributed queue."""
    
    def __init__(self, queue: TaskQueue):
        self.queue = queue
        self.running = False
    
    async def _worker(self) -> None:
        """Worker coroutine processing tasks."""
        while self.running:
            task = await self.queue.dequeue()
            if task:
                start_time = datetime.now()
                try:
                    if task.function:
                        result_val = task.function(*task.args, **task.kwargs)
                        if asyncio.iscoroutine(result_val):
                            result_val = await asyncio.wait_for(result_val, timeout=task.timeout_seconds)
                    else:
                        result_val = None
                    
                    result = TaskResult(task_id=task.task_id, status=TaskState.COMPLETED, output=result_val, started_at=start_time, completed_at=datetime.now())
                except Exception as e:
                    result = TaskResult(task_id=task.task_id, status=TaskState.FAILED, error=str(e), started_at=start_time, completed_at=datetime.now())
                
                await self.queue.mark_completed(task.task_id, result)
            else:
                await asyncio.sleep(0.1)


class DistributedScheduler:
    """Schedule tasks for distributed execution."""
    
    def __init__(self, executor: DistributedExecutor):
        self.executor = executor
        self.scheduled_tasks: Dict[str, DistributedTask] = {}
    
    async def schedule_task(self, function: Callable, args: List[Any] = None, kwargs: Dict[str, Any] = None, priority: int = 0, name: str = "") -> str:
        """Schedule a task for execution."""
        task = DistributedTask(name=name or function.__name__, function=function, args=args or [], kwargs=kwargs or {}, priority=priority)
        task_id = await self.executor.queue.enqueue(task)
        self.scheduled_tasks[task_id] = task
        return task_id
    
    async def wait_for_completion(self, task_id: str, timeout: Optional[float] = None) -> Optional[TaskResult]:
        """Wait for task completion."""
        start = datetime.now()
        while True:
            result = await self.executor.queue.get_result(task_id)
            if result:
                return result
            if timeout and (datetime.now() - start).total_seconds() > timeout:
                return None
            await asyncio.sleep(0.5)
