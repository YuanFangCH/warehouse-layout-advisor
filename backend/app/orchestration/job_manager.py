import threading

from .workflow_runner import run_evaluation


def submit(evaluation_id: str) -> None:
    thread = threading.Thread(target=run_evaluation, args=(evaluation_id,), daemon=True)
    thread.start()
