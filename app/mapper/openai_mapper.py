"""app.mapper.openai_mapper

Mapper implementation that would call OpenAI (placeholder).
"""

from .base import BaseMapper


class OpenAIMapper(BaseMapper):
    def map(self, source):
        return {"mapped": True}
