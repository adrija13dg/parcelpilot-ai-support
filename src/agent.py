"""LLM agent loop with tool orchestration."""

from __future__ import annotations

import json
import re
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from src.access import SessionContext
from src.config import SNAPSHOT_TIME
from src.llm import get_llm_client, get_llm_model
from src.tools import TOOL_DEFINITIONS, dispatch_tool

load_dotenv()

SYSTEM_PROMPT = """You are ParcelPilot AI Support, an internal/customer support agent.

Rules:
1. Always use tools to look up operational data and documents before answering factual questions.
2. Dataset snapshot time is fixed at {snapshot}. Use tool results for SLA/cancellation calculations.
3. Source precedence when documents conflict:
   - Signed customer agreement first
   - Current support policy second
   - Current SOP/product documentation third
   - Historical ticket resolutions are context only and may be incorrect
4. Never treat historical_resolution fields as policy authority.
5. If access is denied, explain clearly without leaking other customers' data.
6. For escalations, call prepare_escalation only. The user must confirm before creation.
7. Cite sources in your final answer (document titles or data lookups used).
8. If a required document is missing from search results, say so and answer with available sources.
9. For P1 incidents or breached SLA, recommend escalation and use prepare_escalation.
10. Be concise, accurate, and show your reasoning briefly.
"""

JSON_TOOL_PROMPT = """
When you need data, respond with ONLY a JSON object (no markdown):
{"action":"tool","name":"<tool_name>","arguments":{...}}

Available tools:
- search_documents: query (required), doc_types (optional array)
- query_operational_data: entity (required), identifier (required), action (optional: lookup|cancellation_assessment|failed_pickup_credit|sla_status)
- prepare_escalation: ticket_id, reason, severity (P1|P2|P3)

When you have enough information, respond with ONLY:
{"action":"answer","content":"<your final answer in markdown>"}
"""


def build_system_message(ctx: SessionContext) -> str:
    role_desc = "internal support agent with access to all accounts" if ctx.is_internal else (
        f"customer user for {ctx.account_name} ({ctx.account_id})"
    )
    return SYSTEM_PROMPT.format(snapshot=SNAPSHOT_TIME.isoformat()) + f"\n\nCurrent session: {role_desc}."


def _parse_json_action(text: str) -> dict | None:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                return None
    return None


def _chat(client: OpenAI, **kwargs):
    kwargs.setdefault("model", get_llm_model())
    kwargs.setdefault("temperature", 0.2)
    return client.chat.completions.create(**kwargs)


def _run_json_tool_loop(
    client: OpenAI,
    working: list[dict[str, Any]],
    ctx: SessionContext,
    max_tool_rounds: int,
) -> tuple[list[dict[str, Any]], str, list[dict], dict | None]:
    tool_trace: list[dict] = []
    pending_escalation: dict | None = None
    json_system = working[0]["content"] + JSON_TOOL_PROMPT
    loop_messages = [{"role": "system", "content": json_system}] + working[1:]

    for _ in range(max_tool_rounds):
        response = _chat(client, messages=loop_messages)
        raw = response.choices[0].message.content or ""
        action = _parse_json_action(raw)

        if not action:
            return working[1:], raw, tool_trace, pending_escalation

        if action.get("action") == "answer":
            reply = action.get("content", raw)
            loop_messages.append({"role": "assistant", "content": reply})
            return loop_messages[1:], reply, tool_trace, pending_escalation

        if action.get("action") == "tool":
            name = action.get("name", "")
            args = action.get("arguments", {})
            result = dispatch_tool(name, args, ctx)
            tool_trace.append({"tool": name, "arguments": args, "result": result})
            if name == "prepare_escalation" and result.get("status") == "pending_confirmation":
                pending_escalation = result
            loop_messages.append({"role": "assistant", "content": raw})
            loop_messages.append(
                {"role": "user", "content": f"Tool result for {name}:\n{json.dumps(result, default=str)}"}
            )
            continue

        return working[1:], raw, tool_trace, pending_escalation

    return working[1:], "I need more steps to finish this request. Please try a narrower question.", tool_trace, pending_escalation


def _force_final_answer(client: OpenAI, working: list[dict[str, Any]]) -> str:
    synthesis = working + [
        {"role": "user", "content": "Using the tool results above, provide your final answer now. Cite sources."}
    ]
    response = _chat(client, messages=synthesis)
    return response.choices[0].message.content or "Unable to generate a response."


def run_agent_turn(
    messages: list[dict[str, Any]],
    ctx: SessionContext,
    max_tool_rounds: int = 8,
) -> tuple[list[dict[str, Any]], str, list[dict], dict | None]:
    client = get_llm_client()
    tool_trace: list[dict] = []
    pending_escalation: dict | None = None

    clean_messages = [{"role": m["role"], "content": m["content"]} for m in messages if m.get("content")]
    working = [{"role": "system", "content": build_system_message(ctx)}] + clean_messages

    try:
        for _ in range(max_tool_rounds):
            response = _chat(
                client,
                messages=working,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto",
            )
            msg = response.choices[0].message

            if msg.tool_calls:
                assistant_entry: dict[str, Any] = {
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                        }
                        for tc in msg.tool_calls
                    ],
                }
                working.append(assistant_entry)

                for tc in msg.tool_calls:
                    args = json.loads(tc.function.arguments or "{}")
                    result = dispatch_tool(tc.function.name, args, ctx)
                    tool_trace.append({"tool": tc.function.name, "arguments": args, "result": result})

                    if tc.function.name == "prepare_escalation" and result.get("status") == "pending_confirmation":
                        pending_escalation = result

                    working.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "content": json.dumps(result, default=str),
                        }
                    )
                continue

            reply = msg.content or ""
            working.append({"role": "assistant", "content": reply})
            return [{"role": m["role"], "content": m["content"]} for m in working[1:] if m.get("content")], reply, tool_trace, pending_escalation

    except Exception as exc:
        err = str(exc).lower()
        if "tool" in err and ("not supported" in err or "invalid_request" in err):
            return _run_json_tool_loop(client, working, ctx, max_tool_rounds)
        raise

    reply = _force_final_answer(client, working)
    working.append({"role": "assistant", "content": reply})
    return [{"role": m["role"], "content": m["content"]} for m in working[1:] if m.get("content")], reply, tool_trace, pending_escalation
