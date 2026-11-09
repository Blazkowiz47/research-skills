# Native host guidance

Read only the section for the active host. Live tool schemas and supported model
settings take precedence over example names here. Use available native tools;
do not install a scheduler, launch nested coding CLIs, or change global settings
to simulate missing capabilities.

## Codex

Keep this skill in the main chat. Use native collaboration actions to spawn,
message, wait for, inspect, and interrupt agents. Where exposed, use
`spawn_agent`, `send_message`, `followup_task`, `wait_agent`, `list_agents`, and
`interrupt_agent` according to their current schemas.

Pass explicit worker `model` and `reasoning_effort` values. Some hosts allow
overrides only with fresh context (`fork_turns="none"`); supply the complete
assignment instead of a full-history fork in that case. Do not rely on parent
inheritance when the user's worker settings differ. Check custom-agent defaults
for conflicting settings before using a named role.

Agents may share the filesystem. Spawning alone does not create an isolated
checkout. Coordinate source and memory writes accordingly. Native subagents are
distinct from creating new user-owned sidebar chats; use subagents for this skill.

See [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents)
for model configuration and native orchestration behavior.

## Claude Code, including its desktop interface

Load this skill in the current conversation, not with `context: fork`: the
current conversation must retain the approved plan and lead role. The shared
`SKILL.md` works through Claude's skill mechanism; `agents/openai.yaml` is Codex
metadata, not a Claude subagent definition.

Use the native Agent tool and available follow-up/completion controls. Supply
the worker contract explicitly; do not assume workers inherit the conversation
or this skill. Use per-invocation model and effort when supported, or a compatible
existing agent definition with those settings. Check host overrides and effective
configuration; if exact settings cannot be honored, report the limitation before
dispatch. Do not change persistent agent configuration without authorization.

Use read-only tool restrictions for critics where available. Worktree isolation
is optional; verify its starting revision includes dependency changes. Ordinary
subagents suffice: this workflow does not require experimental agent teams or
dynamic workflows.

See [Claude subagents](https://code.claude.com/docs/en/sub-agents) for configuration
and [Claude skills](https://code.claude.com/docs/en/skills) for loading behavior.
