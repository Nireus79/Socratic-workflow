# Socratic Workflow - Troubleshooting

## Execution Issues

### Tasks not executing

Cause: Invalid task definition

Solution: Inherit from Task and implement execute()

### Parallel execution not happening

Cause: Incorrect dependencies

Solution: Add tasks without depends_on parameter

## Cost Tracking Issues

### Costs not calculated

Cause: Model name incorrect

Solution: Use exact model names

### Unexpected high costs

Cause: Large model or many tokens

Solution: Use cheaper model

## Performance Issues

### Slow execution

Cause: Tasks running sequentially

Solution: Remove unnecessary dependencies

### High memory usage

Cause: Large task results

Solution: Clear results between tasks
