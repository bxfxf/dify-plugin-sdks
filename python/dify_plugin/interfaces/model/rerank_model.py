import time
from abc import abstractmethod
from typing import Optional

from dify_plugin.entities.model.rerank import RerankResult
from .ai_model import AIModel
from dify_plugin.entities.model import ModelType


class RerankModel(AIModel):
    """
    Base Model class for rerank model.
    """
    model_type: ModelType = ModelType.RERANK

    def _invoke(self, model: str, credentials: dict,
               query: str, docs: list[str], score_threshold: Optional[float] = None, top_n: Optional[int] = None,
               user: Optional[str] = None) \
            -> RerankResult:
        """
        Invoke rerank model

        :param model: model name
        :param credentials: model credentials
        :param query: search query
        :param docs: docs for reranking
        :param score_threshold: score threshold
        :param top_n: top n
        :param user: unique user id
        :return: rerank result
        """
        self.started_at = time.perf_counter()

        try:
            return self.invoke(model, credentials, query, docs, score_threshold, top_n, user)
        except Exception as e:
            raise self._transform_invoke_error(e)

    @abstractmethod
    def invoke(self, model: str, credentials: dict,
                query: str, docs: list[str], score_threshold: Optional[float] = None, top_n: Optional[int] = None,
                user: Optional[str] = None) \
            -> RerankResult:
        """
        Invoke rerank model

        :param model: model name
        :param credentials: model credentials
        :param query: search query
        :param docs: docs for reranking
        :param score_threshold: score threshold
        :param top_n: top n
        :param user: unique user id
        :return: rerank result
        """
        raise NotImplementedError
