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
  // RESTの送信結果とWebSocket通知が同じメッセージでも二重表示しない。
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

  return new Intl.DateTimeFormat("ja-JP", {
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
        // 互いに依存しないルーム情報と履歴は同時に取得する。
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
          throw new Error("このチャットルームを閲覧する権限がありません。");
        }

        if (roomResponse.status === 404 || messagesResponse.status === 404) {
          throw new Error("チャットルームが見つかりませんでした。");
        }

        if (!roomResponse.ok || !messagesResponse.ok) {
          throw new Error("チャット情報を取得できませんでした。");
        }

        const roomData: unknown = await roomResponse.json();
        const messagesData: unknown = await messagesResponse.json();

        if (!isRoomDetail(roomData) || !isMessageList(messagesData)) {
          throw new Error("サーバーから不正なデータを受信しました。");
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
              : "メッセージ履歴を取得できませんでした。",
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
        throw new Error("このチャットルームへ送信する権限がありません。");
      }

      if (response.status === 404) {
        throw new Error("チャットルームが見つかりませんでした。");
      }

      if (!response.ok) {
        throw new Error("メッセージを送信できませんでした。");
      }

      const responseData: unknown = await response.json();

      if (!isMessage(responseData)) {
        throw new Error("サーバーから不正なデータを受信しました。");
      }

      setMessages((currentMessages) =>
        mergeMessage(currentMessages, responseData),
      );
      setMessageContent("");
    } catch (error) {
      setSendErrorMessage(
        error instanceof Error
          ? error.message
          : "メッセージを送信できませんでした。",
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
          <p>メッセージを読み込んでいます...</p>
        </section>
      </main>
    );
  }

  if (errorMessage !== null) {
    return (
      <main className="chat-page">
        <section className="chat-shell error-card">
          <div className="error-symbol" aria-hidden="true">!</div>
          <h1>チャットを開けませんでした</h1>
          <p className="alert alert-error" role="alert">{errorMessage}</p>
          <Link className="primary-button inline-button" href="/home">
            ユーザー一覧へ戻る
          </Link>
        </section>
      </main>
    );
  }

  return (
    <main className="chat-page">
      <section className="chat-shell">
        <header className="chat-header">
          <Link className="back-link" href="/home" aria-label="ユーザー一覧へ戻る">
            ←
          </Link>
          <div className="chat-title">
            <h1>{otherUsername}とのチャット</h1>
          </div>
        </header>

        <div className="message-viewport">
          {messages.length === 0 ? (
            <div className="chat-empty-state">
              <span aria-hidden="true">✦</span>
              <h2>会話を始めましょう</h2>
              <p>最初のメッセージを送ってみてください。</p>
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
              メッセージ
            </label>
            <textarea
              id="message-content"
              name="content"
              value={messageContent}
              onChange={(event) => setMessageContent(event.target.value)}
              onKeyDown={handleTextareaKeyDown}
              maxLength={2000}
              rows={1}
              placeholder="メッセージを入力"
              aria-describedby="composer-help"
              disabled={isSending}
              required
            />
            <button
              className="send-button"
              type="submit"
              disabled={isSending || messageContent.trim().length === 0}
              aria-label="メッセージを送信"
            >
              {isSending ? "…" : "送信"}
            </button>
          </form>
          <div id="composer-help" className="composer-help">
            <span>Enterで送信・Shift + Enterで改行</span>
            <span>{messageContent.length}/2000</span>
          </div>
        </footer>
      </section>
    </main>
  );
}
