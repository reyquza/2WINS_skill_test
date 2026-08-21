import ChatRoom from "@/components/ChatRoom";


type ChatRoomPageProps = {
  params: Promise<{
    room_id: string;
  }>;
};


export default async function ChatRoomPage({
  params,
}: ChatRoomPageProps) {
  const { room_id } = await params;

  return (
    <ChatRoom
      key={room_id}
      roomId={room_id}
    />
  );
}
