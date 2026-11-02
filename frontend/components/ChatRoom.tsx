"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  useEffect,
  useRef,
  useState,
  type FormEvent,
  type KeyboardEvent,
} from "react";

import { getCurrentUser } from "@/lib/auth";
import { API_BASE_URL, WS_BASE_URL } from "@/lib/config";
import {
  isMessage,
  isMessageCreatedEvent,
  isMessageList,
  type Message,
} from "@/types/message";
import { isRoomDetail } from "@/types/room";


type ChatRoomProps = {
  roomId: string;
};

function mergeMessage(
  currentMessages: Message[],
  incomingMessage: Message,
): Message[] {
  // The REST response and WebSocket event may contain the same message.
  const alreadyExists = currentMessages.some(
    (message) => message.id === incomingMessage.id,
  );

  if (alreadyExists) {
    return currentMessages;
  }

  return [...currentMessages, incomingMessage].sort(
    (firstMessage, secondMessage) =>
      firstMessage.id - secondMessage.id,
  );
}


function formatMessageTime(value: string): string {
  const includesTimeZone = /(?:Z|[+-]\d{2}:\d{2})$/.test(value);
  const normalizedValue = includesTimeZone ? value : `${value}Z`;
  const date = new Date(normalizedValue);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "numeric",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}


export default function ChatRoom({ roomId }: ChatRoomProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [otherUsername, setOtherUsername] = useState("");
  const [currentUserId, setCurrentUserId] = useState<number | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [messageContent, setMessageContent] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const [sendErrorMessage, setSendErrorMessage] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const router = useRouter();

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "end",
    });
  }, [messages]);

  useEffect(() => {
    let isCancelled = false;

    async function loadMessages(): Promise<void> {
      try {
        const currentUser = await getCurrentUser();
        if (currentUser === null) {
          router.replace("/login");
          return;
        }

        const authenticatedUserId = currentUser.id;
        // Room metadata and history are independent, so load them concurrently.
        const [roomResponse, messagesResponse] = await Promise.all([
          fetch(`${API_BASE_URL}/api/rooms/${roomId}`, {
            credentials: "include",
          }),
          fetch(`${API_BASE_URL}/api/rooms/${roomId}/messages`, {
            credentials: "include",
          }),
        ]);

        if (roomResponse.status === 401 || messagesResponse.status === 401) {
          router.replace("/login");
          return;
        }

        if (roomResponse.status === 403 || messagesResponse.status === 403) {
          throw new Error("You do not have access to this conversation.");
        }

        if (roomResponse.status === 404 || messagesResponse.status === 404) {
          throw new Error("This conversation could not be found.");
        }

        if (!roomResponse.ok || !messagesResponse.ok) {
          throw new Error("We could not load this conversation.");
        }

        const roomData: unknown = await roomResponse.json();
        const messagesData: unknown = await messagesResponse.json();

        if (!isRoomDetail(roomData) || !isMessageList(messagesData)) {
          throw new Error("The server returned an invalid response.");
        }

        if (!isCancelled) {
          setCurrentUserId(authenticatedUserId);
          setOtherUsername(roomData.other_user.username);
          setMessages(messagesData);
        }
      } catch (error) {
        if (!isCancelled) {
          setErrorMessage(
            error instanceof Error
              ? error.message
              : "We could not load the message history.",
          );
        }
      } finally {
        if (!isCancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadMessages();

    return () => {
      isCancelled = true;
    };
  }, [roomId, router]);

  useEffect(() => {
    if (currentUserId === null || errorMessage !== null) {
      return;
    }

    let socket: WebSocket | null = null;
    let reconnectTimerId: number | null = null;
    let reconnectAttempt = 0;
    let shouldReconnect = true;

    async function synchronizeMessages() {
      try {
        const response = await fetch(
          `${API_BASE_URL}/api/rooms/${roomId}/messages`,
          { credentials: "include" },
        );

        if (!response.ok) {
          return;
        }

        const responseData: unknown = await response.json();

        if (!isMessageList(responseData)) {
          return;
        }

        setMessages((currentMessages) =>
          responseData.reduce(
            (mergedMessages, message) =>
              mergeMessage(mergedMessages, message),
            currentMessages,
          ),
        );
      } catch {
        return;
      }
    }

    function connectWebSocket() {
      socket = new WebSocket(`${WS_BASE_URL}/ws/rooms/${roomId}`);

      socket.addEventListener("open", () => {
        reconnectAttempt = 0;
        void synchronizeMessages();
      });

      socket.addEventListener("message", (event: MessageEvent<string>) => {
        try {
          const receivedData: unknown = JSON.parse(event.data);

          if (
            !isMessageCreatedEvent(receivedData) ||
            receivedData.data.room_id !== Number(roomId)
          ) {
            return;
          }

          setMessages((currentMessages) =>
            mergeMessage(currentMessages, receivedData.data),
          );
        } catch {
          return;
        }
      });

      socket.addEventListener("close", (event: CloseEvent) => {
        const wasRejectedByServer = event.code === 1008;

        if (!shouldReconnect) {
          return;
        }

        if (wasRejectedByServer) {
          return;
        }

        const reconnectDelay = Math.min(
          1000 * 2 ** reconnectAttempt,
          8000,
        );
        reconnectAttempt += 1;
        reconnectTimerId = window.setTimeout(connectWebSocket, reconnectDelay);
      });
    }

    connectWebSocket();

    return () => {
      shouldReconnect = false;

      if (reconnectTimerId !== null) {
        window.clearTimeout(reconnectTimerId);
      }

      socket?.close();
    };
  }, [currentUserId, errorMessage, roomId]);

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ): Promise<void> {
    event.preventDefault();
    const trimmedContent = messageContent.trim();

    if (
      trimmedContent.length === 0 ||
      isSending ||
      currentUserId === null
    ) {
      return;
    }

    setIsSending(true);
    setSendErrorMessage(null);

    try {
      const response = await fetch(
        `${API_BASE_URL}/api/rooms/${roomId}/messages`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          credentials: "include",
          body: JSON.stringify({ content: trimmedContent }),
        },
      );

      if (response.status === 401) {
        router.replace("/login");
        return;
      }

      if (response.status === 403) {
        throw new Error("You do not have permission to send messages here.");
      }

      if (response.status === 404) {
        throw new Error("This conversation could not be found.");
      }

      if (!response.ok) {
        throw new Error("We could not send your message.");
      }

      const responseData: unknown = await response.json();

      if (!isMessage(responseData)) {
        throw new Error("The server returned an invalid response.");
      }

      setMessages((currentMessages) =>
        mergeMessage(currentMessages, responseData),
      );
      setMessageContent("");
    } catch (error) {
      setSendErrorMessage(
        error instanceof Error
          ? error.message
          : "We could not send your message.",
      );
    } finally {
      setIsSending(false);
    }
  }

  function handleTextareaKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      event.currentTarget.form?.requestSubmit();
    }
  }

  if (isLoading) {
    return (
      <main className="chat-page">
        <section className="chat-shell loading-card" aria-live="polite">
          <div className="loading-spinner" aria-hidden="true" />
          <p>Loading messages...</p>
        </section>
      </main>
    );
  }

  if (errorMessage !== null) {
    return (
      <main className="chat-page">
        <section className="chat-shell error-card">
          <div className="error-symbol" aria-hidden="true">!</div>
          <h1>Unable to open conversation</h1>
          <p className="alert alert-error" role="alert">{errorMessage}</p>
          <Link className="primary-button inline-button" href="/home">
            Back to people
          </Link>
        </section>
      </main>
    );
  }

  return (
    <main className="chat-page">
      <section className="chat-shell">
        <header className="chat-header">
          <Link className="back-link" href="/home" aria-label="Back to people">
            ←
          </Link>
          <div className="chat-title">
            <h1>Chat with {otherUsername}</h1>
          </div>
        </header>

        <div className="message-viewport">
          {messages.length === 0 ? (
            <div className="chat-empty-state">
              <span aria-hidden="true">✦</span>
              <h2>Start the conversation</h2>
              <p>Send the first message to say hello.</p>
            </div>
          ) : (
            <ol className="message-list" aria-live="polite">
              {messages.map((message) => {
                const isOwnMessage = message.sender_id === currentUserId;

                return (
                  <li
                    className={isOwnMessage ? "message-row own-message" : "message-row"}
                    key={message.id}
                  >
                    <div className="message-meta">
                      <time dateTime={message.created_at}>
                        {formatMessageTime(message.created_at)}
                      </time>
                    </div>
                    <p className="message-bubble">{message.content}</p>
                  </li>
                );
              })}
            </ol>
          )}
          <div ref={messagesEndRef} />
        </div>

        <footer className="composer-area">
          {sendErrorMessage && (
            <p className="alert alert-error composer-error" role="alert">
              {sendErrorMessage}
            </p>
          )}

          <form className="composer-form" onSubmit={handleSubmit}>
            <label className="visually-hidden" htmlFor="message-content">
              Message
            </label>
            <textarea
              id="message-content"
              name="content"
              value={messageContent}
              onChange={(event) => setMessageContent(event.target.value)}
              onKeyDown={handleTextareaKeyDown}
              maxLength={2000}
              rows={1}
              placeholder="Write a message"
              aria-describedby="composer-help"
              disabled={isSending}
              required
            />
            <button
              className="send-button"
              type="submit"
              disabled={isSending || messageContent.trim().length === 0}
              aria-label="Send message"
            >
              {isSending ? "…" : "Send"}
            </button>
          </form>
          <div id="composer-help" className="composer-help">
            <span>Enter to send · Shift + Enter for a new line</span>
            <span>{messageContent.length}/2000</span>
          </div>
        </footer>
      </section>
    </main>
  );
}
