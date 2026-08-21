import { isUser, type User } from "@/types/user";


export type Room = {
  id: number;
  created_at: string;
};


export type RoomDetail = Room & {
  other_user: User;
};


export function isRoom(value: unknown): value is Room {
  if (typeof value !== "object" || value === null) {
    return false;
  }

  const room = value as Record<string, unknown>;

  return (
    Number.isInteger(room.id) &&
    typeof room.created_at === "string"
  );
}


export function isRoomDetail(value: unknown): value is RoomDetail {
  if (!isRoom(value)) {
    return false;
  }

  const room = value as unknown as Record<string, unknown>;
  return isUser(room.other_user);
}
