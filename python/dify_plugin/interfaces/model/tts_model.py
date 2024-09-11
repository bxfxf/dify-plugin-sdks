from collections.abc import Generator
import hashlib
import logging
import re
import subprocess
import uuid
from abc import abstractmethod
from typing import Any, Optional

from pydantic import ConfigDict

from .ai_model import AIModel
from dify_plugin.errors.model import InvokeBadRequestError
from dify_plugin.entities.model import ModelPropertyKey, ModelType


logger = logging.getLogger(__name__)


class TTSModel(AIModel):
    """
    Model class for ttstext model.
    """

    model_type: ModelType = ModelType.TTS

    # pydantic configs
    model_config = ConfigDict(protected_namespaces=())

    def _invoke(
        self,
        model: str,
        credentials: dict,
        content_text: str,
        voice: str,
        user: Optional[str] = None,
    ) -> bytes | Generator[bytes, None, None]:
        """
        Invoke large language model

        :param model: model name
        :param tenant_id: user tenant id
        :param credentials: model credentials
        :param voice: model timbre
        :param content_text: text content to be translated
        :param streaming: output is streaming
        :param user: unique user id
        :return: translated audio file
        """
        try:
            logger.info(f"Invoke TTS model: {model} , invoke content : {content_text}")
            self._is_ffmpeg_installed()
            return self.invoke(
                model=model,
                credentials=credentials,
                user=user,
                content_text=content_text,
                voice=voice,
            )
        except Exception as e:
            raise self._transform_invoke_error(e)

    @abstractmethod
    def invoke(
        self,
        model: str,
        credentials: dict,
        content_text: str,
        voice: str,
        user: Optional[str] = None,
    ) -> bytes | Generator[bytes, None, None]:
        """
        Invoke large language model

        :param model: model name
        :param tenant_id: user tenant id
        :param credentials: model credentials
        :param voice: model timbre
        :param content_text: text content to be translated
        :param streaming: output is streaming
        :param user: unique user id
        :return: translated audio file
        """
        raise NotImplementedError

    def get_tts_model_voices(
        self, model: str, credentials: dict, language: Optional[str] = None
    ) -> Optional[list]:
        """
        Get voice for given tts model voices

        :param language: tts language
        :param model: model name
        :param credentials: model credentials
        :return: voices lists
        """
        model_schema = self.get_model_schema(model, credentials)

        if model_schema and ModelPropertyKey.VOICES in model_schema.model_properties:
            voices = model_schema.model_properties[ModelPropertyKey.VOICES]
            if language:
                return [
                    {"name": d["name"], "value": d["mode"]}
                    for d in voices
                    if language and language in d.get("language")
                ]
            else:
                return [{"name": d["name"], "value": d["mode"]} for d in voices]

    def _get_model_default_voice(self, model: str, credentials: dict) -> Any:
        """
        Get voice for given tts model

        :param model: model name
        :param credentials: model credentials
        :return: voice
        """
        model_schema = self.get_model_schema(model, credentials)

        if (
            model_schema
            and ModelPropertyKey.DEFAULT_VOICE in model_schema.model_properties
        ):
            return model_schema.model_properties[ModelPropertyKey.DEFAULT_VOICE]

    def _get_model_audio_type(self, model: str, credentials: dict) -> Optional[str]:
        """
        Get audio type for given tts model

        :param model: model name
        :param credentials: model credentials
        :return: voice
        """
        model_schema = self.get_model_schema(model, credentials)

        if (
            model_schema
            and ModelPropertyKey.AUDIO_TYPE in model_schema.model_properties
        ):
            return model_schema.model_properties[ModelPropertyKey.AUDIO_TYPE]

    def _get_model_word_limit(self, model: str, credentials: dict) -> Optional[int]:
        """
        Get audio type for given tts model
        :return: audio type
        """
        model_schema = self.get_model_schema(model, credentials)

        if (
            model_schema
            and ModelPropertyKey.WORD_LIMIT in model_schema.model_properties
        ):
            return model_schema.model_properties[ModelPropertyKey.WORD_LIMIT]

    def _get_model_workers_limit(self, model: str, credentials: dict) -> Optional[int]:
        """
        Get audio max workers for given tts model
        :return: audio type
        """
        model_schema = self.get_model_schema(model, credentials)

        if (
            model_schema
            and ModelPropertyKey.MAX_WORKERS in model_schema.model_properties
        ):
            return model_schema.model_properties[ModelPropertyKey.MAX_WORKERS]

    @staticmethod
    def _split_text_into_sentences(org_text, max_length=2000, pattern=r"[。.!?]"):
        match = re.compile(pattern)
        tx = match.finditer(org_text)
        start = 0
        result = []
        one_sentence = ""
        for i in tx:
            end = i.regs[0][1]
            tmp = org_text[start:end]
            if len(one_sentence + tmp) > max_length:
                result.append(one_sentence)
                one_sentence = ""
            one_sentence += tmp
            start = end
        last_sens = org_text[start:]
        if last_sens:
            one_sentence += last_sens
        if one_sentence != "":
            result.append(one_sentence)
        return result

    @staticmethod
    def _is_ffmpeg_installed():
        try:
            output = subprocess.check_output("ffmpeg -version", shell=True)
            if "ffmpeg version" in output.decode("utf-8"):
                return True
            else:
                raise InvokeBadRequestError(
                    "ffmpeg is not installed, "
                    "details: https://docs.dify.ai/getting-started/install-self-hosted"
                    "/install-faq#id-14.-what-to-do-if-this-error-occurs-in-text-to-speech"
                )
        except Exception:
            raise InvokeBadRequestError(
                "ffmpeg is not installed, "
                "details: https://docs.dify.ai/getting-started/install-self-hosted"
                "/install-faq#id-14.-what-to-do-if-this-error-occurs-in-text-to-speech"
            )

    # Todo: To improve the streaming function
    @staticmethod
    def _get_file_name(file_content: str) -> str:
        hash_object = hashlib.sha256(file_content.encode())
        hex_digest = hash_object.hexdigest()

        namespace_uuid = uuid.UUID("a5da6ef9-b303-596f-8e88-bf8fa40f4b31")
        unique_uuid = uuid.uuid5(namespace_uuid, hex_digest)
        return str(unique_uuid)
