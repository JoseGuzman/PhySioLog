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

from flask_login import UserMixin
from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

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


class AdminClientAssignment(db.Model):
    """Association table mapping admins to the users they manage."""

    __tablename__ = "admin_client_assignments"
    __table_args__ = (
        UniqueConstraint(
            "admin_user_id",
            "client_user_id",
            name="uix_admin_client_assignment",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    admin_user_id: Mapped[int] = mapped_column(
        db.ForeignKey("users.id"), nullable=False, index=True
    )
    client_user_id: Mapped[int] = mapped_column(
        db.ForeignKey("users.id"), nullable=False, index=True
    )


class User(UserMixin, db.Model):
    """Database model for users."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str | None] = mapped_column(db.String(100), nullable=True, index=True)
    age: Mapped[int | None] = mapped_column(nullable=True)
    height_cm: Mapped[float | None] = mapped_column(nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(nullable=True)
    email: Mapped[str] = mapped_column(db.String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(db.String(255), nullable=False)
    is_active_user: Mapped[bool] = mapped_column(default=True, nullable=False)
    is_admin: Mapped[bool] = mapped_column(default=False, nullable=False)
    has_subscription: Mapped[bool] = mapped_column(default=False, nullable=False)

    entries: Mapped[list[HealthEntry]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def set_password(self, password: str) -> None:
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Check if the provided password matches the stored hash."""
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self) -> bool:
        """Return whether the user is active."""
        return self.is_active_user


class HealthEntry(db.Model):
    """Database model for daily health tracking entries."""

    __tablename__ = "health_entries"
    __table_args__ = (UniqueConstraint("user_id", "date", name="uix_user_date"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(
        db.ForeignKey("users.id"), nullable=False, index=True
    )
    # The date of the entry is not unique, allowing for multiple users
    date: Mapped[Date] = mapped_column(unique=False, nullable=False, index=True)
    # Relationship back to User
    user: Mapped[User] = relationship(back_populates="entries")

    # this is optional, as users may not want to track all metrics every day
    weight_kg: Mapped[float | None] = mapped_column(nullable=True)
    body_fat_percent: Mapped[float | None] = mapped_column(nullable=True)
    calories_kcal: Mapped[int | None] = mapped_column(nullable=True)
    protein_g: Mapped[int | None] = mapped_column(nullable=True)
    steps_count: Mapped[int | None] = mapped_column(nullable=True)
    sleep_hours: Mapped[float | None] = mapped_column(nullable=True)

    # if user trains, they can log the total training volume (weight x reps)
    training_volume_kg: Mapped[int | None] = mapped_column(nullable=True)

    # For sentiment analysis
    sleep_quality: Mapped[str | None] = mapped_column(db.String(20), nullable=True)
    observations: Mapped[str | None] = mapped_column(db.Text, nullable=True)

    @property
    def fat_mass_kg(self) -> float | None:
        """Derived fat mass from weight and body fat percentage."""
        if self.weight_kg is None or self.body_fat_percent is None:
            return None
        return round(self.weight_kg * self.body_fat_percent / 100, 2)

    @property
    def lean_mass_kg(self) -> float | None:
        """Derived lean mass from total weight minus fat mass."""
        fat_mass = self.fat_mass_kg
        if self.weight_kg is None or fat_mass is None:
            return None
        return round(self.weight_kg - fat_mass, 2)

    @property
    def fat_mass_change(self) -> float | None:
        """Difference in fat mass compared with the previous entry for the same user."""
        current_fat_mass = self.fat_mass_kg
        if current_fat_mass is None:
            return None

        previous_entry = (
            HealthEntry.query.filter(
                HealthEntry.user_id == self.user_id,
                HealthEntry.date < self.date,
            )
            .order_by(HealthEntry.date.desc())
            .first()
        )
        if previous_entry is None or previous_entry.fat_mass_kg is None:
            return None

        return round(current_fat_mass - previous_entry.fat_mass_kg, 2)

    @property
    def fat_mass_change_7d(self) -> float | None:
        """
        Average daily fat-mass change across the last 7 entries, ignoring missing values.
        This value is more stable than the day-to-day change, which can be noisy
        due to water retention and other factors.

        Assuming 1 Kg of fat requires energy equivalent of 7700 kcal, we can
        estimate the maintenance calories by simply total calories - fat_mass_change * 7700.
        (see maintenance_kcal() )
        """
        current_fat_mass = self.fat_mass_kg
        if current_fat_mass is None:
            return None

        previous_entries = (
            HealthEntry.query.filter(
                HealthEntry.user_id == self.user_id,
                HealthEntry.date < self.date,
            )
            .order_by(HealthEntry.date.desc())
            .limit(7)
            .all()
        )

        previous_fat_values = [
            entry.fat_mass_kg
            for entry in reversed(previous_entries)
            if entry.fat_mass_kg is not None
        ]
        if not previous_fat_values:
            return None

        baseline_fat_mass = previous_fat_values[0]
        valid_days = len(previous_fat_values)
        return round((current_fat_mass - baseline_fat_mass) / valid_days, 3)

    @property
    def calories_kcal_7d(self) -> float | None:
        """Average calories across the last 7 entries, ignoring missing values."""
        entries = (
            HealthEntry.query.filter(
                HealthEntry.user_id == self.user_id,
                HealthEntry.date <= self.date,
            )
            .order_by(HealthEntry.date.desc())
            .limit(7)
            .all()
        )

        calories_values = [
            entry.calories_kcal
            for entry in reversed(entries)
            if entry.calories_kcal is not None
        ]
        if not calories_values:
            return None

        return round(sum(calories_values) / len(calories_values), 2)

    @property
    def maintenance_kcal(self) -> int | None:
        """
        Estimated maintenance calories from intake and fat-mass trend.
        maintenance calories = calories_kcal_7d - (fat_mass_change_7d * CONSTANT)

        CONSTANT is adapted from 
        Max Wishnofsky, “Caloric equivalents of gained or lost weight,” 
        The American Journal of Clinical Nutrition (1958), DOI: 10.1093/ajcn/6.5.542
        """
        # fat energy equivalent
        KCAL_PER_KG_FAT = 7700

        if self.calories_kcal_7d is None or self.fat_mass_change_7d is None:
            return None

        return int(
            round(self.calories_kcal_7d - (self.fat_mass_change_7d * KCAL_PER_KG_FAT))
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize the entry into JSON-friendly primitives."""
        return {
            "id": self.id,
            "date": self.date.strftime("%Y-%m-%d"),
            "weight_kg": self.weight_kg,
            "body_fat_percent": self.body_fat_percent,
            "fat_mass_kg": self.fat_mass_kg,
            "fat_mass_change": self.fat_mass_change,
            "fat_mass_change_7d": self.fat_mass_change_7d,
            "calories_kcal_7d": self.calories_kcal_7d,
            "maintenance_kcal": self.maintenance_kcal,
            "lean_mass_kg": self.lean_mass_kg,
            "calories_kcal": self.calories_kcal,
            "protein_g": self.protein_g,
            "training_volume_kg": self.training_volume_kg,
            "steps_count": self.steps_count,
            "sleep_hours": _decimal_hours_to_hhmm(self.sleep_hours),
            "sleep_hours_decimal": self.sleep_hours,
            "sleep_quality": self.sleep_quality,
            "observations": self.observations,
        }
