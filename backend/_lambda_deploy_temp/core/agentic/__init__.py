"""
Agentic AI module - parallel specialist agent orchestration
5 specialist agents analyze races concurrently via ThreadPoolExecutor.
"""

try:
    from .orchestrator import run_orchestration, AgentOutput
except ImportError:
    def run_orchestration(*args, **kwargs):
        return {}
    AgentOutput = None

try:
    from .lambda_wrapper import lambda_handler as agentic_lambda_handler
except ImportError:
    pass

__all__ = [
    'run_orchestration',
    'AgentOutput',
]

