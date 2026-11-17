"""Shared in-process session identity, frozen retry payload and atomic persistence."""
from copy import deepcopy
from datetime import datetime
from uuid import uuid4

from .typing_engine import TypingEngine


class SessionController:
    def __init__(self):
        self.reset()

    def reset(self):
        if getattr(self, "pending", None) is not None and not self.saved:
            raise RuntimeError("Save the pending session before starting another")
        self.identity = uuid4().hex
        self.pending = None
        self.saved = False
        self.completed = False
        self.clock = TypingEngine()
        self.clock.reset("session")

    def persist(self, record, ctx, completed=False):
        if self.saved:
            return
        if self.pending is None:
            self.pending = deepcopy(record)
            self.pending.session_uid = self.identity
            self.pending.finished_at = record.finished_at or datetime.now().isoformat(timespec="seconds")
            self.completed = completed
        record = self.pending
        if record.total_chars == 0:
            self.saved = True
            return
        from .achievements import check_and_unlock
        with ctx.stats_repo.db.transaction():
            ctx.stats_repo.save_session(record)
            if self.completed and record.mode == "lesson":
                ctx.lesson_repo.mark_completed(record.mode_detail, record.wpm, record.accuracy)
            check_and_unlock(
                ctx.stats_repo, ctx.achievement_repo,
                lesson_count=len(ctx.lesson_repo.get_mastered()),
                streak=ctx.stats_repo.get_streak(),
            )
        self.saved = True
