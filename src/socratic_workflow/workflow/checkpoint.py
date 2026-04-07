"""Incremental workflow execution with checkpointing support."""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class CheckpointMetadata:
    """Metadata for a workflow checkpoint."""

    checkpoint_id: str
    workflow_name: str
    created_at: str
    last_completed_task: str
    total_tasks_completed: int
    total_tasks_failed: int
    version: int = 1
    description: str = ""
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "checkpoint_id": self.checkpoint_id,
            "workflow_name": self.workflow_name,
            "created_at": self.created_at,
            "last_completed_task": self.last_completed_task,
            "total_tasks_completed": self.total_tasks_completed,
            "total_tasks_failed": self.total_tasks_failed,
            "version": self.version,
            "description": self.description,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CheckpointMetadata":
        """Create from dictionary."""
        return cls(
            checkpoint_id=data["checkpoint_id"],
            workflow_name=data["workflow_name"],
            created_at=data["created_at"],
            last_completed_task=data["last_completed_task"],
            total_tasks_completed=data["total_tasks_completed"],
            total_tasks_failed=data["total_tasks_failed"],
            version=data.get("version", 1),
            description=data.get("description", ""),
            tags=data.get("tags", []),
        )


class CheckpointManager:
    """Manages workflow checkpoints for incremental execution."""

    def __init__(self, checkpoint_dir: str = ".workflow_checkpoints"):
        """
        Initialize checkpoint manager.

        Args:
            checkpoint_dir: Directory to store checkpoints
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def create_checkpoint(
        self,
        workflow_name: str,
        task_results: Dict[str, Dict[str, Any]],
        task_status: Dict[str, str],
        execution_errors: Dict[str, str],
        description: str = "",
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        Create a checkpoint from current workflow state.

        Args:
            workflow_name: Name of the workflow
            task_results: Completed task results
            task_status: Status of each task
            execution_errors: Any execution errors
            description: Optional checkpoint description
            tags: Optional tags for grouping checkpoints

        Returns:
            Checkpoint ID
        """
        checkpoint_id = f"{workflow_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Find last completed task
        completed_tasks = [
            task_id for task_id, status in task_status.items() if status == "completed"
        ]
        last_completed = completed_tasks[-1] if completed_tasks else None

        metadata = CheckpointMetadata(
            checkpoint_id=checkpoint_id,
            workflow_name=workflow_name,
            created_at=datetime.now().isoformat(),
            last_completed_task=last_completed or "",
            total_tasks_completed=len(completed_tasks),
            total_tasks_failed=len(execution_errors),
            description=description,
            tags=tags or [],
        )

        checkpoint_data = {
            "metadata": metadata.to_dict(),
            "task_results": task_results,
            "task_status": task_status,
            "execution_errors": execution_errors,
        }

        # Save checkpoint
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.json"

        try:
            with open(checkpoint_path, "w") as f:
                json.dump(checkpoint_data, f, indent=2)
            self.logger.info(f"Checkpoint created: {checkpoint_id}")
            return checkpoint_id
        except IOError as e:
            self.logger.error(f"Failed to create checkpoint {checkpoint_id}: {e}")
            raise

    def load_checkpoint(self, checkpoint_id: str) -> Dict[str, Any]:
        """
        Load checkpoint by ID.

        Args:
            checkpoint_id: ID of the checkpoint to load

        Returns:
            Checkpoint data dictionary

        Raises:
            FileNotFoundError: If checkpoint doesn't exist
            json.JSONDecodeError: If checkpoint file is corrupted
        """
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.json"

        if not checkpoint_path.exists():
            raise FileNotFoundError(f"Checkpoint not found: {checkpoint_id}")

        try:
            with open(checkpoint_path, "r") as f:
                data = json.load(f)
            self.logger.info(f"Checkpoint loaded: {checkpoint_id}")
            return data
        except IOError as e:
            self.logger.error(f"Failed to load checkpoint {checkpoint_id}: {e}")
            raise
        except json.JSONDecodeError as e:
            self.logger.error(f"Corrupted checkpoint file {checkpoint_id}: {e}")
            raise

    def list_checkpoints(
        self,
        workflow_name: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[CheckpointMetadata]:
        """
        List available checkpoints.

        Args:
            workflow_name: Optional filter by workflow name
            tags: Optional filter by tags (any match)

        Returns:
            List of checkpoint metadata
        """
        checkpoints = []

        for checkpoint_file in self.checkpoint_dir.glob("*.json"):
            try:
                with open(checkpoint_file, "r") as f:
                    data = json.load(f)
                    metadata = CheckpointMetadata.from_dict(data["metadata"])

                    # Apply filters
                    if workflow_name and metadata.workflow_name != workflow_name:
                        continue

                    if tags and not any(t in metadata.tags for t in tags):
                        continue

                    checkpoints.append(metadata)
            except (IOError, json.JSONDecodeError, KeyError):
                self.logger.warning(f"Skipping corrupted checkpoint: {checkpoint_file}")
                continue

        # Sort by creation time (newest first)
        checkpoints.sort(key=lambda c: c.created_at, reverse=True)
        return checkpoints

    def get_latest_checkpoint(
        self,
        workflow_name: str,
    ) -> Optional[CheckpointMetadata]:
        """
        Get the latest checkpoint for a workflow.

        Args:
            workflow_name: Name of the workflow

        Returns:
            Latest checkpoint metadata or None if no checkpoints exist
        """
        checkpoints = self.list_checkpoints(workflow_name=workflow_name)
        return checkpoints[0] if checkpoints else None

    def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Delete a checkpoint.

        Args:
            checkpoint_id: ID of checkpoint to delete

        Returns:
            True if deleted, False if not found
        """
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.json"

        if not checkpoint_path.exists():
            return False

        try:
            checkpoint_path.unlink()
            self.logger.info(f"Checkpoint deleted: {checkpoint_id}")
            return True
        except IOError as e:
            self.logger.error(f"Failed to delete checkpoint {checkpoint_id}: {e}")
            return False

    def cleanup_old_checkpoints(
        self,
        workflow_name: str,
        keep_count: int = 5,
    ) -> int:
        """
        Delete old checkpoints, keeping only the most recent.

        Args:
            workflow_name: Name of the workflow
            keep_count: Number of recent checkpoints to keep

        Returns:
            Number of checkpoints deleted
        """
        checkpoints = self.list_checkpoints(workflow_name=workflow_name)

        if len(checkpoints) <= keep_count:
            return 0

        deleted_count = 0
        for checkpoint in checkpoints[keep_count:]:
            if self.delete_checkpoint(checkpoint.checkpoint_id):
                deleted_count += 1

        self.logger.info(f"Cleaned up {deleted_count} old checkpoints for {workflow_name}")
        return deleted_count

    def tag_checkpoint(
        self,
        checkpoint_id: str,
        tags: List[str],
    ) -> bool:
        """
        Add tags to an existing checkpoint.

        Args:
            checkpoint_id: ID of checkpoint to tag
            tags: Tags to add

        Returns:
            True if successful, False otherwise
        """
        try:
            checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.json"
            if not checkpoint_path.exists():
                return False

            with open(checkpoint_path, "r") as f:
                data = json.load(f)

            metadata = CheckpointMetadata.from_dict(data["metadata"])
            metadata.tags.extend(tags)
            metadata.tags = list(set(metadata.tags))  # Remove duplicates
            data["metadata"] = metadata.to_dict()

            with open(checkpoint_path, "w") as f:
                json.dump(data, f, indent=2)

            return True
        except (IOError, json.JSONDecodeError):
            return False

    def get_checkpoint_size(self, checkpoint_id: str) -> int:
        """
        Get size of checkpoint file in bytes.

        Args:
            checkpoint_id: ID of checkpoint

        Returns:
            Size in bytes, or 0 if not found
        """
        checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.json"

        if checkpoint_path.exists():
            return checkpoint_path.stat().st_size

        return 0

    def export_checkpoint(
        self,
        checkpoint_id: str,
        export_path: str,
    ) -> bool:
        """
        Export a checkpoint to an external location.

        Args:
            checkpoint_id: ID of checkpoint to export
            export_path: Path to export to

        Returns:
            True if successful, False otherwise
        """
        try:
            checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.json"
            if not checkpoint_path.exists():
                return False

            with open(checkpoint_path, "r") as f:
                data = json.load(f)

            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)

            with open(export_file, "w") as f:
                json.dump(data, f, indent=2)

            self.logger.info(f"Checkpoint exported: {checkpoint_id} -> {export_path}")
            return True
        except (IOError, json.JSONDecodeError) as e:
            self.logger.error(f"Failed to export checkpoint: {e}")
            return False

    def import_checkpoint(
        self,
        import_path: str,
        checkpoint_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        Import a checkpoint from an external location.

        Args:
            import_path: Path to checkpoint file to import
            checkpoint_id: Optional custom ID for imported checkpoint

        Returns:
            Checkpoint ID if successful, None otherwise
        """
        try:
            with open(import_path, "r") as f:
                data = json.load(f)

            metadata = CheckpointMetadata.from_dict(data["metadata"])
            if checkpoint_id:
                metadata.checkpoint_id = checkpoint_id
            else:
                checkpoint_id = (
                    f"{metadata.checkpoint_id}_imported_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                )
                metadata.checkpoint_id = checkpoint_id

            data["metadata"] = metadata.to_dict()

            checkpoint_path = self.checkpoint_dir / f"{checkpoint_id}.json"
            with open(checkpoint_path, "w") as f:
                json.dump(data, f, indent=2)

            self.logger.info(f"Checkpoint imported: {checkpoint_id}")
            return checkpoint_id
        except (IOError, json.JSONDecodeError, KeyError) as e:
            self.logger.error(f"Failed to import checkpoint: {e}")
            return None
