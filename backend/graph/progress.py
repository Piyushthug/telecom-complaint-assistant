"""Thread-safe progress tracker for LangGraph nodes.

As each node in the workflow executes, we record its completion so the
frontend can display real-time progress.
"""
import json
from dataclasses import dataclass, asdict
from queue import Queue
from typing import Optional

@dataclass
class ProgressEvent:
    step: str
    status: str  # "started" or "completed"
    message: str
    timestamp: float = 0.0


class ProgressTracker:
    def __init__(self):
        self.queue: Queue = Queue()

    def record(self, step: str, status: str, message: str) -> None:
        import time
        event = ProgressEvent(
            step=step,
            status=status,
            message=message,
            timestamp=time.time()
        )
        self.queue.put(event)

    def get_event(self) -> Optional[ProgressEvent]:
        try:
            return self.queue.get_nowait()
        except:
            return None

    def clear(self) -> None:
        while not self.queue.empty():
            try:
                self.queue.get_nowait()
            except:
                break
