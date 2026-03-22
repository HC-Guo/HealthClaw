# 开发工作流技能 SOP
> 代码审查、CI/CD、项目管理、文档工具、调试、Git
> 包含 17 个 OpenClaw skill 的压缩迁移。

---

### dispatching-parallel-agents
**用途**: Use when facing 2+ independent tasks that can be worked on without shared state or sequential dependencies
**触发条件**: related"];; shared state"];; - 3+ test files failing with different root causes; Multiple subsystems broken independently
```
Agent 1 → Fix agent-tool-abort.test.ts
Agent 2 → Fix batch-completion-behavior.test.ts
Agent 3 → Fix tool-approval-race-conditions.test.ts
```

### executing-plans
**用途**: Use when you have a written implementation plan to execute in a separate session with review checkpoints

### finishing-a-development-branch
**用途**: Use when implementation is complete, all tests pass, and you need to decide how to integrate the work - guides completion of development work by presenting structured options for merge, PR, or cleanup
```
git worktree remove <worktree-path>
```

### goal-analyzer
**用途**: 分析健康目标数据、识别目标模式、评估目标进度,并提供个性化目标管理建议。支持与营养、运动、睡眠等健康数据的关联分析。
```
{
  "habit": "morning-stretch",
  "current_streak": 21,
  "longest_streak": 21,
  "completion_rate": 95.2,
  "strength_score": 7.5,
  "stage": "巩固期",
  "assessment": "习惯即将形成,继续保持!",
  "next_milestone": 30,
  "suggestions": [
    "继续保持,即将达到30天里程碑",
    "可以尝试添加新的相关习惯"
  ]
}
```

### performance-profiling
**用途**: Identify computational bottlenecks, analyze scaling behavior, estimate memory requirements, and receive optimization recommendations for any computational simulation. Use when simulations are slow,...
```
python3 scripts/timing_analyzer.py --log simulation.log --json
```
**限制**: **Log parsing**: Depends on pattern matching; may miss unusual formats; **Scaling analysis**: Requires at least 2 runs for meaningful results

### receiving-code-review
**用途**: Use when receiving code review feedback, before implementing suggestions, especially if feedback seems unclear or technically questionable - requires technical rigor and verification, not performat...
```
Reviewer: "Remove legacy code"
❌ "You're absolutely right! Let me remove that..."
```

### requesting-code-review
**用途**: Use when completing tasks, implementing major features, or before merging to verify work meets requirements
```
BASE_SHA=$(git rev-parse HEAD~1)  # or origin/main
HEAD_SHA=$(git rev-parse HEAD)
```

### search-strategy
**用途**: 
```
query: "What is the status of project aurora?"
```

### slurm-job-script-generator
**用途**: Generate SLURM `sbatch` job scripts and sanity-check HPC resource requests (nodes, tasks, CPUs, memory, GPUs) for simulation runs. Use when preparing submission scripts, deciding MPI vs MPI+OpenMP ...
```
python3 scripts/slurm_script_generator.py --job-name run --time 02:00:00 --nodes 2 --ntasks-per-node 64 --cpus-per-task 2 -- -- ./simulate
```
**限制**: Does not query cluster hardware or site policies; it can only validate internal consistency.; SLURM installations vary (GPU directives, QoS rules, partitions). Adjust directives for your site.

### subagent-driven-development
**用途**: Use when executing implementation plans with independent tasks in the current session
**触发条件**: tightly coupled"];; parallel session"];; - Same session (no context switch); Fresh subagent per task (no context pollution)
```
digraph when_to_use {
    "Have implementation plan?" [shape=diamond];
    "Tasks mostly independent?" [shape=diamond];
    "Stay in this session?" [shape=diamond];
    "subagent-driven-development" [shape=box];
    "executing-plans" [shape=box];
    "Manual execution or brainstorm first" [shape=box];

    "Have implementation plan?" -> "Tasks mostly independent?" [label="yes"];
    "Have implementation plan?" -> "Manual execution or brainstorm first" [label="no"];
    "Tasks mostly independent?
# ... (truncated)
```

### systematic-debugging
**用途**: Use when encountering any bug, test failure, or unexpected behavior, before proposing fixes
**触发条件**: Test failures; Bugs in production; Unexpected behavior; Performance problems
```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

### test-driven-development
**用途**: Use when implementing any feature or bugfix, before writing implementation code
**触发条件**: - New features; Bug fixes; Refactoring; Behavior changes
```
$ npm test
PASS
```

### using-git-worktrees
**用途**: Use when starting feature work that needs isolation from current workspace or before executing implementation plans - creates isolated git worktrees with smart directory selection and safety verifi...
```
grep -i "worktree.*director" CLAUDE.md 2>/dev/null
```

### using-superpowers
**用途**: Use when starting any conversation - establishes how to find and use skills, requiring Skill tool invocation before ANY response including clarifying questions
```
digraph skill_flow {
    "User message received" [shape=doublecircle];
    "About to EnterPlanMode?" [shape=doublecircle];
    "Already brainstormed?" [shape=diamond];
    "Invoke brainstorming skill" [shape=box];
    "Might any skill apply?" [shape=diamond];
    "Invoke Skill tool" [shape=box];
    "Announce: 'Using [skill] to [purpose]'" [shape=box];
    "Has checklist?" [shape=diamond];
    "Create TodoWrite todo per item" [shape=box];
    "Follow skill exactly" [shape=box];
    "Respond (inc
# ... (truncated)
```

### verification-before-completion
**用途**: Use when about to claim work is complete, fixed, or passing, before committing or creating PRs - requires running verification commands and confirming output before making any success claims; evide...
```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

### writing-plans
**用途**: Use when you have a spec or requirements for a multi-step task, before touching code
```

```

### writing-skills
**用途**: Use when creating new skills, editing existing skills, or verifying skills work before deployment
```
Write code before test? Delete it.
```
