from app.domain.enums import ClockStatus
from app.domain.models import Clock


class ClockService:
    def advance(self, clock: Clock, amount: int) -> bool:
        if clock.status != ClockStatus.ACTIVE:
            return False

        was_completed = clock.current_segments >= clock.max_segments

        clock.current_segments = min(
            clock.current_segments + amount,
            clock.max_segments,
        )

        is_completed = clock.current_segments >= clock.max_segments

        if is_completed:
            clock.status = ClockStatus.COMPLETED
            clock.effects_applied = False

        return is_completed and not was_completed

    def reduce(self, clock: Clock, amount: int) -> None:
        clock.current_segments = max(clock.current_segments - amount, 0)

        if clock.current_segments < clock.max_segments:
            clock.status = ClockStatus.ACTIVE
            clock.effects_applied = False