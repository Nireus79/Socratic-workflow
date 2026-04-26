# socratic-workflow Architecture

Production-grade workflow orchestration with cost tracking and dependency management.

## System Overview

socratic-workflow provides workflow definition and execution management. It enables:
- Definition of multi-node workflow graphs
- Path enumeration and optimization
- Cost tracking and prediction
- Risk calculation and mitigation
- Error recovery and resumption
- State management and versioning

## Core Components

### 1. WorkflowNode

Represents a step or decision point in a workflow:
- `node_id` - Unique identifier
- `node_type` - WorkflowNodeType enum:
  - PHASE_START - Workflow entry point
  - QUESTION_SET - Question collection phase
  - ANALYSIS - Analysis/processing phase
  - DECISION - Decision point
  - PHASE_END - Workflow completion
  - VALIDATION - Validation step
- `label` - Human-readable description
- `estimated_tokens` - Expected LLM token usage
- `questions` - Associated questions if applicable
- `metadata` - Custom data (e.g., AI model, parameters)

### 2. WorkflowEdge

Represents transitions between nodes:
- `from_node` - Source node ID
- `to_node` - Target node ID
- `probability` - Likelihood of this edge being taken
- `condition` - Optional condition for edge traversal
- `cost` - Cost of traversing this edge in tokens

### 3. WorkflowDefinition

Complete workflow structure:
- `workflow_id` - Unique identifier
- `name` - Human-readable name
- `phase` - Current project phase (discovery/analysis/design/implementation)
- `nodes` - Dict mapping node_id to WorkflowNode
- `edges` - List of WorkflowEdge transitions
- `start_node` - Entry point ID
- `end_nodes` - Possible exit points (plural for conditional workflows)
- `strategy` - Decision strategy for path selection

### 4. WorkflowPath

Calculated path through workflow with metrics:
- `path_id` - Unique path identifier
- `nodes` - Ordered list of node IDs in path
- `edges` - Ordered list of edge IDs in path
- `total_cost_tokens` - Estimated token usage
- `total_cost_usd` - Estimated USD cost
- `risk_score` - Overall risk (0.0-1.0)
- `rework_probability` - Chance rework needed
- `incompleteness_risk` - Risk of incomplete results
- `complexity_risk` - Risk from complexity
- `category_coverage` - Dict of category completion %
- `missing_categories` - Categories not covered
- `quality_score` - Predicted output quality (0.0-1.0)
- `expected_maturity_gain` - Project maturity improvement
- `roi_score` - Return on investment score

### 5. PathDecisionStrategy

Strategy for selecting optimal path:
- `MINIMIZE_COST` - Select lowest-cost path
- `MINIMIZE_RISK` - Select lowest-risk path
- `BALANCED` - Balance cost and risk
- `MAXIMIZE_QUALITY` - Prioritize quality over cost
- `USER_CHOICE` - Present all paths to user

### 6. WorkflowApprovalRequest

Request for workflow path approval:
- `request_id` - Unique request ID
- `project_id` - Associated project
- `phase` - Current project phase
- `workflow` - WorkflowDefinition
- `all_paths` - All possible paths enumerated
- `recommended_path` - Best path per strategy
- `strategy` - Which strategy was used
- `requested_by` - User/agent requesting
- `status` - pending/approved/rejected
- `approved_path_id` - Which path was approved
- `approval_timestamp` - When approval occurred

### 7. WorkflowExecutionState

Current execution state during workflow run:
- `execution_id` - Unique execution ID
- `workflow_id` - Workflow being executed
- `approved_path_id` - Which path is being executed
- `current_node_id` - Current node in path
- `completed_nodes` - Nodes already executed
- `remaining_nodes` - Nodes still to execute
- `actual_tokens_used` - Tokens actually consumed
- `estimated_tokens_remaining` - Remaining budget
- `started_at` - Execution start timestamp
- `status` - active/completed/paused

## Workflow Execution Flow

```
1. Define Workflow
   - Create nodes (PHASE_START, ANALYSIS, DECISION, etc.)
   - Define edges with costs and conditions
   - Create WorkflowDefinition

2. Enumerate Paths
   - Find all possible paths from start to end
   - Calculate metrics for each path:
     - Total token cost
     - Risk score
     - Quality prediction
     - ROI score

3. Request Approval
   - Create WorkflowApprovalRequest
   - Present recommended path + alternatives
   - Apply selected strategy

4. Execute Workflow
   - Initialize WorkflowExecutionState
   - Process current node
   - Move to next node
   - Track actual costs vs. estimate

5. Handle Errors
   - Capture execution errors
   - Initiate recovery
   - Optionally restart from checkpoint

6. Complete
   - Mark workflow complete
   - Record actual metrics
   - Update project state
```

## Dependency Resolution

Workflow handles inter-node dependencies:
1. **Sequential Dependencies** - Node B only after Node A completes
2. **Conditional Dependencies** - Node B only if condition met
3. **Parallel Dependencies** - Multiple nodes run simultaneously
4. **Fan-out/Fan-in** - One node triggers multiple, collect results

## Cost Tracking Integration

```
Node Cost Estimation
    |
    v
Path Cost Calculation (sum of nodes)
    |
    v
Workflow Cost Tracking
    |
    v
Actual Cost vs. Estimate
    |
    v
Learning for Future Workflows
```

## Error Recovery Mechanism

```
Node Execution
    |
    v
Error Detected?
    |---> No ---> Proceed to next node
    |
    Yes
    |
    v
Error Type?
    |
    +---> Recoverable ---> Retry with backoff
    |
    +---> Checkpoint exists ---> Resume from checkpoint
    |
    +---> Fatal ---> Mark workflow failed

Capture:
- Error message
- Node state
- Execution context
- Estimated impact
```

## State Transitions

```
PENDING (created)
    |
    v
ACTIVE (started)
    |
    +---> PAUSED (manual pause)
    |     |
    |     v
    |     ACTIVE (resumed)
    |
    +---> COMPLETED (all nodes finished)
    |
    +---> FAILED (unrecoverable error)

Each transition records timestamp and context.
```

## Integration Points

### With socratic-nexus (LLM Client)
- Token estimation based on actual model costs
- Track LLM calls through workflow
- Optimize prompts within nodes

### With socratic-analyzer (Code Analysis)
- Analyze code in ANALYSIS nodes
- Provide analysis results to DECISION nodes
- Track code quality metrics

### With socratic-maturity (Maturity Tracking)
- Estimate maturity gain per path
- Select paths that advance maturity
- Track maturity improvement

### With socratic-learning (Learning System)
- Record workflow outcomes
- Learn from past executions
- Improve cost/risk estimates

### With socratic-agents (Agent Framework)
- Agents create/modify workflows
- Agents make decisions at DECISION nodes
- Multi-agent workflow coordination

## Performance Characteristics

- **Path Enumeration**: O(2^n) worst case (exponential branching)
- **Cost Calculation**: O(n) where n = nodes in path
- **Risk Calculation**: O(n)
- **Memory**: O(p*n) where p = number of paths, n = avg path length

## Extension Points

### Custom Node Types
```python
class CustomNodeType(Enum):
    CUSTOM = "custom"

# Add to WorkflowNodeType
```

### Custom Decision Strategies
```python
class CustomStrategy(PathDecisionStrategy):
    CUSTOM = "custom"
```

### Custom Metrics
```python
# Extend WorkflowPath with domain-specific metrics
```

---

Part of the Socratic Ecosystem | Graph-Based Workflow | Cost-Aware Execution
