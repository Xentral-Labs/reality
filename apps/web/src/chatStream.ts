export type ChatReply = {
  user: { id: string; content: string };
  assistant: { id: string; content: string };
};
export type ChatStreamEvent =
  | { type: "start" | "reset" }
  | { type: "delta"; text: string }
  | ({ type: "done" } & ChatReply)
  | { type: "error"; message: string };

/** Decode response fragments without losing split UTF-8 characters or replaying sends. */
export async function readChatStream(
  response: Response,
  onEvent: (event: ChatStreamEvent) => void,
): Promise<ChatReply> {
  if (!response.body) throw new Error("Chat response is incomplete. Reload to check its status.");
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  try {
    while (true) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value, { stream: !done });
      let newline: number;
      while ((newline = buffer.indexOf("\n")) !== -1) {
        const line = buffer.slice(0, newline).trim();
        buffer = buffer.slice(newline + 1);
        if (!line) continue;
        const event = JSON.parse(line) as ChatStreamEvent;
        if (event.type === "error") throw new Error(event.message);
        if (event.type === "done") {
          if (
            !event.user?.id ||
            !event.assistant?.id ||
            typeof event.user.content !== "string" ||
            typeof event.assistant.content !== "string"
          )
            throw new Error("Chat response is incomplete. Reload to check its status.");
          onEvent(event);
          return event;
        }
        if (
          event.type === "reset" ||
          event.type === "start" ||
          (event.type === "delta" && typeof event.text === "string")
        )
          onEvent(event);
      }
      if (done) break;
    }
    throw new Error("Chat response is incomplete. Reload to check its status.");
  } finally {
    await reader.cancel().catch(() => undefined);
    reader.releaseLock();
  }
}
