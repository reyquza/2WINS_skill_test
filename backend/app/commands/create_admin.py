import argparse
from getpass import getpass

from pydantic import ValidationError
from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError

from app.database import SessionLocal
from app.models import User
from app.schemas import RegisterRequest
from app.security import hash_password


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create an administrator account",
    )
    parser.add_argument("--username", required=True)
    parser.add_argument("--email", required=True)
    args = parser.parse_args()

    password = getpass("Password: ")
    password_confirmation = getpass("Confirm password: ")
    if password != password_confirmation:
        parser.error("Passwords do not match")

    try:
        admin_data = RegisterRequest(
            username=args.username,
            email=args.email,
            password=password,
        )
    except ValidationError as exc:
        parser.error(str(exc))

    normalized_email = str(admin_data.email).lower()

    with SessionLocal() as db:
        duplicate_stmt = select(User).where(
            or_(
                User.username == admin_data.username,
                User.email == normalized_email,
            )
        )
        if db.scalars(duplicate_stmt).one_or_none() is not None:
            parser.error("Username or email is already registered")

        admin = User(
            username=admin_data.username,
            email=normalized_email,
            password_hash=hash_password(admin_data.password),
            is_admin=True,
        )
        db.add(admin)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            parser.error("Username or email is already registered")

        print(f"Administrator created: {admin.username} ({admin.email})")


if __name__ == "__main__":
    main()
