"""
models.py

See here: https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-iv-database
and maybe this too:
https://www.digitalocean.com/community/tutorials/how-to-use-flask-sqlalchemy-to-interact-with-databases-in-a-flask-application

Author: Jose Guzman, sjm.guzman<at>gmail.com
Created: Fri Feb 13 09:20:23 CET 2026

Usage:
------

To test table creation, run the following commands in the python shell:
>>> from physiolog.models import User
>>> u = User(name='Jose', email='jose.guzman@example.com')
>>> u.__dict__
>>> {'_sa_instance_state': <sqlalchemy.orm.state.InstanceState at 0x1088b80a0>,
    'name': 'Jose',
    'email': 'jose.guzman@example.com'}
>>> u
name: Jose
"""

from __future__ import annotations  # python 3.12 uses [type|type]

from datetime import date as Date

from sqlalchemy.orm import Mapped, mapped_column

from .extensions import db


def _decimal_hours_to_hhmm(value: float | None) -> str | None:
    """Convert decimal hours to HH:MM format."""
    if value is None:
        return None

    hours = int(value)
    minutes = round((value - hours) * 60)
    if minutes == 60:
        hours += 1
        minutes = 0
    return f"{hours:02d}:{minutes:02d}"


class HealthEntry(db.Model):
    """Database model for daily health tracking entries."""

    __tablename__ = "health_entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[Date] = mapped_column(unique=True, nullable=False, index=True)

    weight: Mapped[float | None] = mapped_column(nullable=True)
    body_fat: Mapped[float | None] = mapped_column(nullable=True)
    calories: Mapped[float | None] = mapped_column(nullable=True)
    training_volume: Mapped[float | None] = mapped_column(nullable=True)
    steps: Mapped[int | None] = mapped_column(nullable=True)
    sleep_total: Mapped[float | None] = mapped_column(nullable=True)

    sleep_quality: Mapped[str | None] = mapped_column(db.String(20), nullable=True)
    observations: Mapped[str | None] = mapped_column(db.Text, nullable=True)

    def to_dict(self) -> dict[str, object]:
        """Serialize the entry into JSON-friendly primitives."""
        return {
            "id": self.id,
            "date": self.date.strftime("%Y-%m-%d"),
            "weight": self.weight,
            "body_fat": self.body_fat,
            "calories": self.calories,
            "training_volume": self.training_volume,
            "steps": self.steps,
            "sleep_total": _decimal_hours_to_hhmm(self.sleep_total),
            "sleep_total_decimal": self.sleep_total,
            "sleep_quality": self.sleep_quality,
            "observations": self.observations,
        }
