import logging
from abc import abstractmethod

from src.models.enums.integration_status import IntegrationStatus
from src.integration_downloads.model_caching import ModelCache


class Handler(ModelCache):

    def __init__(self):
        super().__init__()
        self._requires_file = False
        pass

    def process(self, context):
        logging.info('Starting %s' % self.__class__.__name__)
        video = self._get_context_value(context, 'video', require=False)
        if video is not None and self._requires_file and video.integration_status != IntegrationStatus.COMPLETE.value:
            logging.info('Finished %s' % self.__class__.__name__)
            return
        self._handle(context)
        logging.info('Finished %s' % self.__class__.__name__)

    def _get_context_value(self, context, name, or_raise=None, require=True, default=None):
        value = context.get(name, default) if context.get(name, default) is not None else default
        if not value and or_raise:
            raise Exception(or_raise)
        if not value and require:
            raise Exception('Required context value %s not set' % name)
        return value

    def _set_context_value(self, context, name, value):
        context[name] = value
        
    

    @abstractmethod
    def _handle(self, context):
        pass