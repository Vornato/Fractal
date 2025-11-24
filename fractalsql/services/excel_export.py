from pathlib import Path

import pandas as pd
from filelock import FileLock
from flask import current_app

from models import User, UserStatus


def write_users_to_excel() -> str:
    """
    Snapshot all users into the configured Excel file.
    """
    output_path = Path(current_app.config["G:\Fractal\fractalsql\Database"])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lock = FileLock(str(output_path) + ".lock")

    try:
        with current_app.app_context():
            users = User.query.order_by(User.created_at.asc()).all()
            data = []
            for user in users:
                data.append(
                    {
                        "Name": user.name,
                        "Email": user.email,
                        "Phone": user.phone,
                        "ID": user.id_number,
                        "DOB": user.dob.isoformat() if user.dob else "",
                        "Gender": user.gender or "",
                        "Social": user.social_link or "",
                        "City": user.city or "",
                        "Status": user.status.value if user.status else UserStatus.TEMPORARY.value,
                        "Updated": user.updated_at.isoformat() if user.updated_at else "",
                    }
                )

            df = pd.DataFrame(
                data,
                columns=["Name", "Email", "Phone", "ID", "DOB", "Gender", "Social", "City", "Status", "Updated"],
            )

            with lock:
                df.to_excel(output_path, index=False, engine="openpyxl")
    except Exception:
        current_app.logger.exception("Failed to write users Excel snapshot to %s", output_path)

    return str(output_path)
