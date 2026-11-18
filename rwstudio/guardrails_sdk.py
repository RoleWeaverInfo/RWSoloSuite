"""Local Guardrails AI validators; no model judge, remote validation or reasks."""
import os
import threading
from importlib.metadata import version

os.environ['OTEL_SDK_DISABLED']='true'
os.environ['LITELLM_LOCAL_MODEL_COST_MAP']='True'
os.environ['GUARDRAILS_RUN_SYNC']='true'
from guardrails import Guard
from guardrails.validators import Validator, register_validator, PassResult, FailResult
from .guardrails import reason


@register_validator(name='roleweaver-solo/gameplay-dialogue',data_type='string')
class DialoguePolicy(Validator):
    def _validate(self,value,metadata):
        code=reason(value,metadata['direction'],metadata['settings'],metadata.get('instructions',''))
        return FailResult(error_message=code) if code else PassResult()


class LocalValidation:
    version=version('guardrails-ai')
    def __init__(self):self.local=threading.local()

    def validate(self,text,direction,settings,instructions):
        guard=getattr(self.local,'guard',None)
        if guard is None:
            guard=Guard(use_server=False,history_max_length=1)
            guard.configure(allow_metrics_collection=False)
            guard.use(DialoguePolicy(on_fail='noop',use_local=True))
            self.local.guard=guard
        try:
            outcome=guard.validate(text,metadata=dict(direction=direction,settings=settings,instructions=instructions),num_reasks=0)
            return '' if outcome.validation_passed else reason(text,direction,settings,instructions) or 'validation_failed'
        finally:guard.history.clear()
