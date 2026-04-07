"""Pre-built workflow templates for common Socratic patterns."""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class WorkflowTemplate:
    """Pre-built workflow template."""

    template_id: str
    name: str
    description: str
    version: str = "1.0.0"
    category: str = "general"
    definition: Dict[str, Any] = field(default_factory=dict)
    parameters: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)


class WorkflowTemplateLibrary:
    """Library of pre-built workflow templates."""

    def __init__(self):
        """Initialize template library."""
        self.templates: Dict[str, WorkflowTemplate] = {}
        self._register_default_templates()

    def _register_default_templates(self) -> None:
        """Register default Socratic workflow templates."""

        # Socratic Question Generation Workflow
        self.register_template(
            WorkflowTemplate(
                template_id="socratic_question_gen",
                name="Socratic Question Generation",
                description="Generate guided questions for user learning",
                category="questioning",
                definition={
                    "name": "Socratic Question Generation",
                    "steps": [
                        {
                            "id": "analyze_context",
                            "agent": "ContextAnalyzer",
                            "description": "Analyze user context and knowledge level",
                            "params": {"user_id": "${user_id}", "project_id": "${project_id}"},
                        },
                        {
                            "id": "generate_questions",
                            "agent": "SocraticCounselor",
                            "description": "Generate targeted Socratic questions",
                            "depends_on": ["analyze_context"],
                            "params": {"context": "${analyze_context.output}"},
                        },
                        {
                            "id": "rank_questions",
                            "agent": "QualityController",
                            "description": "Rank questions by effectiveness",
                            "depends_on": ["generate_questions"],
                            "params": {"questions": "${generate_questions.output}"},
                        },
                    ],
                },
                parameters={
                    "user_id": {"type": "string", "required": True},
                    "project_id": {"type": "string", "required": True},
                    "question_count": {"type": "integer", "default": 3},
                    "difficulty_level": {"type": "string", "default": "adaptive"},
                },
            )
        )

        # Code Review Workflow
        self.register_template(
            WorkflowTemplate(
                template_id="code_review",
                name="Code Review Workflow",
                description="Comprehensive code review and feedback",
                category="code_quality",
                definition={
                    "name": "Code Review",
                    "steps": [
                        {
                            "id": "validate_code",
                            "agent": "CodeValidator",
                            "description": "Validate code syntax and structure",
                            "params": {"code": "${code}"},
                        },
                        {
                            "id": "analyze_quality",
                            "agent": "CodeAnalyzer",
                            "description": "Analyze code quality metrics",
                            "depends_on": ["validate_code"],
                            "params": {"code": "${code}"},
                        },
                        {
                            "id": "detect_issues",
                            "agent": "CodeSmellDetector",
                            "description": "Detect code smells and anti-patterns",
                            "depends_on": ["validate_code"],
                            "params": {"code": "${code}"},
                        },
                        {
                            "id": "generate_feedback",
                            "agent": "CodeGenerator",
                            "description": "Generate improvement suggestions",
                            "depends_on": ["analyze_quality", "detect_issues"],
                            "params": {
                                "issues": "${detect_issues.output}",
                                "metrics": "${analyze_quality.output}",
                            },
                        },
                    ],
                },
                parameters={
                    "code": {"type": "string", "required": True},
                    "language": {"type": "string", "default": "python"},
                    "strict_mode": {"type": "boolean", "default": False},
                },
            )
        )

        # Project Analysis Workflow
        self.register_template(
            WorkflowTemplate(
                template_id="project_analysis",
                name="Project Analysis Workflow",
                description="Complete project analysis and recommendations",
                category="analysis",
                definition={
                    "name": "Project Analysis",
                    "steps": [
                        {
                            "id": "gather_metrics",
                            "agent": "MetricsCollector",
                            "description": "Gather project metrics",
                            "params": {"project_id": "${project_id}"},
                        },
                        {
                            "id": "analyze_progress",
                            "agent": "ProjectManager",
                            "description": "Analyze project progress and maturity",
                            "depends_on": ["gather_metrics"],
                            "params": {"metrics": "${gather_metrics.output}"},
                        },
                        {
                            "id": "generate_insights",
                            "agent": "KnowledgeAnalyzer",
                            "description": "Generate insights from analysis",
                            "depends_on": ["analyze_progress"],
                            "params": {"analysis": "${analyze_progress.output}"},
                        },
                        {
                            "id": "create_recommendations",
                            "agent": "RecommendationEngine",
                            "description": "Create actionable recommendations",
                            "depends_on": ["generate_insights"],
                            "params": {"insights": "${generate_insights.output}"},
                        },
                    ],
                },
                parameters={
                    "project_id": {"type": "string", "required": True},
                    "depth": {
                        "type": "string",
                        "default": "standard",
                        "enum": ["quick", "standard", "deep"],
                    },
                },
            )
        )

        # Learning Path Workflow
        self.register_template(
            WorkflowTemplate(
                template_id="learning_path",
                name="Personalized Learning Path",
                description="Create personalized learning path for user",
                category="learning",
                definition={
                    "name": "Learning Path Generation",
                    "steps": [
                        {
                            "id": "profile_user",
                            "agent": "UserLearning",
                            "description": "Build user learning profile",
                            "params": {"user_id": "${user_id}"},
                        },
                        {
                            "id": "identify_goals",
                            "agent": "SocraticCounselor",
                            "description": "Identify learning goals",
                            "depends_on": ["profile_user"],
                            "params": {"profile": "${profile_user.output}"},
                        },
                        {
                            "id": "design_path",
                            "agent": "LearningPathDesigner",
                            "description": "Design personalized learning path",
                            "depends_on": ["identify_goals"],
                            "params": {"goals": "${identify_goals.output}"},
                        },
                        {
                            "id": "track_progress",
                            "agent": "UserLearning",
                            "description": "Set up progress tracking",
                            "depends_on": ["design_path"],
                            "params": {"path": "${design_path.output}"},
                        },
                    ],
                },
                parameters={
                    "user_id": {"type": "string", "required": True},
                    "target_skill": {"type": "string", "required": True},
                    "duration_weeks": {"type": "integer", "default": 4},
                },
            )
        )

        # Collaborative Review Workflow
        self.register_template(
            WorkflowTemplate(
                template_id="collaborative_review",
                name="Collaborative Review",
                description="Multi-agent collaborative review and consensus",
                category="collaboration",
                definition={
                    "name": "Collaborative Review",
                    "steps": [
                        {
                            "id": "distribute_reviews",
                            "agent": "WorkflowOrchestrator",
                            "description": "Distribute review to multiple agents",
                            "params": {"content": "${content}"},
                        },
                        {
                            "id": "collect_feedback",
                            "agent": "CollaborationManager",
                            "description": "Collect feedback from all reviewers",
                            "depends_on": ["distribute_reviews"],
                            "params": {"reviews": "${distribute_reviews.output}"},
                        },
                        {
                            "id": "resolve_conflicts",
                            "agent": "ConflictResolver",
                            "description": "Resolve conflicting opinions",
                            "depends_on": ["collect_feedback"],
                            "params": {"feedback": "${collect_feedback.output}"},
                        },
                        {
                            "id": "generate_consensus",
                            "agent": "SocraticCounselor",
                            "description": "Generate consensus output",
                            "depends_on": ["resolve_conflicts"],
                            "params": {"resolution": "${resolve_conflicts.output}"},
                        },
                    ],
                },
                parameters={
                    "content": {"type": "string", "required": True},
                    "reviewer_count": {"type": "integer", "default": 3},
                    "consensus_threshold": {"type": "number", "default": 0.7},
                },
            )
        )

        logger.info(f"Registered {len(self.templates)} default workflow templates")

    def register_template(self, template: WorkflowTemplate) -> None:
        """
        Register a workflow template.

        Args:
            template: Workflow template to register
        """
        self.templates[template.template_id] = template
        logger.info(f"Registered template: {template.template_id} ({template.name})")

    def get_template(self, template_id: str) -> Optional[WorkflowTemplate]:
        """
        Get workflow template by ID.

        Args:
            template_id: Template ID

        Returns:
            Workflow template or None
        """
        return self.templates.get(template_id)

    def get_templates_by_category(self, category: str) -> List[WorkflowTemplate]:
        """
        Get templates by category.

        Args:
            category: Category name

        Returns:
            List of templates in category
        """
        return [t for t in self.templates.values() if t.category == category]

    def instantiate_workflow(
        self,
        template_id: str,
        **parameters,
    ) -> Dict[str, Any]:
        """
        Create workflow instance from template.

        Args:
            template_id: Template ID
            **parameters: Parameter values for workflow

        Returns:
            Workflow definition with parameters substituted
        """
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        # Validate parameters
        for param_name, param_spec in template.parameters.items():
            if param_spec.get("required") and param_name not in parameters:
                raise ValueError(f"Required parameter missing: {param_name}")

        # Create workflow instance
        workflow = {
            "workflow_id": f"{template_id}_{datetime.utcnow().timestamp()}",
            "template_id": template_id,
            "name": template.name,
            "definition": self._substitute_parameters(
                template.definition,
                parameters,
            ),
            "parameters": parameters,
            "created_at": datetime.utcnow().isoformat(),
        }

        logger.info(f"Instantiated workflow from template: {template_id}")
        return workflow

    def _substitute_parameters(self, obj: Any, parameters: Dict[str, Any]) -> Any:
        """Recursively substitute parameters in object."""
        if isinstance(obj, dict):
            return {k: self._substitute_parameters(v, parameters) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._substitute_parameters(item, parameters) for item in obj]
        elif isinstance(obj, str):
            # Replace ${param} with parameter value
            result = obj
            for param_name, param_value in parameters.items():
                result = result.replace(f"${{{param_name}}}", str(param_value))
            return result
        return obj

    def list_templates(self) -> List[Dict[str, Any]]:
        """List all available templates."""
        return [
            {
                "template_id": t.template_id,
                "name": t.name,
                "description": t.description,
                "category": t.category,
                "version": t.version,
            }
            for t in self.templates.values()
        ]

    def export_template(self, template_id: str) -> Dict[str, Any]:
        """Export template as JSON."""
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")

        return {
            "template_id": template.template_id,
            "name": template.name,
            "description": template.description,
            "version": template.version,
            "category": template.category,
            "definition": template.definition,
            "parameters": template.parameters,
            "created_at": template.created_at,
        }
