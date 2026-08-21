export type Message = {
  id: number;
  room_id: number;
  sender_id: number;
  content: string;
  created_at: string;
};

export type MessageCreatedEvent = {
  type: "message.created";
  data: Message;
};

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}


export function isMessage(value: unknown): value is Message {
  return (
    isRecord(value) &&
    Number.isInteger(value.id) &&
    Number.isInteger(value.room_id) &&
    Number.isInteger(value.sender_id) &&
    typeof value.content === "string" &&
    typeof value.created_at === "string"
  );
}


export function isMessageList(value: unknown): value is Message[] {
  return Array.isArray(value) && value.every(isMessage);
}

export function isMessageCreatedEvent(
  value: unknown,
): value is MessageCreatedEvent {
  if (!isRecord(value) || value.type !== "message.created") {
    return false;
  }

  if (!isMessage(value.data)) {
    return false;
  }

  return true;
}
