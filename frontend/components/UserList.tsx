import type { User } from "@/types/user";

type UserListProps = {
  users: User[];
  onSelectUser: (user: User) => void;
  openingUserId: number | null;
};


export default function UserList({
  users,
  onSelectUser,
  openingUserId,
}: UserListProps) {
  return (
    <section className="user-section" aria-labelledby="user-list-title">
      <div className="section-heading">
        <div>
          <h2 id="user-list-title">People</h2>
          <p>Choose someone to start a conversation.</p>
        </div>
      </div>

      {users.length === 0 ? (
        <div className="empty-state">
          <span className="empty-icon" aria-hidden="true">＋</span>
          <p>No one else is here yet.</p>
          <small>Other active accounts will appear here.</small>
        </div>
      ) : (
        <ul className="user-list">
          {users.map((user) => (
            <li className="user-row" key={user.id}>
              <div className="user-summary">
                <span className="user-avatar" aria-hidden="true">
                  {user.username.charAt(0).toUpperCase()}
                </span>
                <span className="user-name">{user.username}</span>
              </div>
              <button
                className="chat-button"
                type="button"
                onClick={() => onSelectUser(user)}
                disabled={openingUserId !== null}
              >
                {openingUserId === user.id
                  ? "Opening..."
                  : "Start chat →"}
              </button>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
