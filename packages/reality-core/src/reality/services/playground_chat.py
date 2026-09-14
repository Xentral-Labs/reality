"""Stateless, owner-scoped sandbox explanations through the shared Copilot."""

import asyncio
import os

from sqlalchemy.orm import Session

from reality.services.core import InvalidOperation
from reality.services.tenant_policy import playground_chat_scope


def ask(
    session: Session,
    user_id: str,
    run_id: str,
    message: str,
    history: list[dict[str, str]],
) -> dict:
    from reality.agent.mcp_chat import reply_via_anthropic_tools

    with playground_chat_scope(session, user_id, run_id) as run:
        if not message.strip() or len(message) > 4000 or len(history) > 12:
            raise InvalidOperation("Invalid companion message.")
        if any(
            row.get("role") not in {"user", "assistant"}
            or len(row.get("content", "")) > 4000
            for row in history
        ):
            raise InvalidOperation("Invalid companion history.")
        key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
        if not key:
            raise InvalidOperation("The managed assistant is not configured.")
        from reality.services.free_playground import reserve_managed_question

        reserve_managed_question(session, run.tenant_id, user_id, companion=True)
        try:
            # Reservation committed; bind read-only authority to the new transaction.
            with playground_chat_scope(session, user_id, run_id):
                answer = asyncio.run(
                    reply_via_anthropic_tools(
                        session=session,
                        tenant_id=run.tenant_id,
                        api_key=key,
                        workspace_id=os.environ.get(
                            "ANTHROPIC_WORKSPACE_ID", ""
                        ).strip(),
                        history=history,
                        message=message.strip(),
                    )
                )
        except Exception as error:
            raise InvalidOperation(
                "The assistant could not answer. Please try again."
            ) from error
        return {"answer": answer}
