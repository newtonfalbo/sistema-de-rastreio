from rest_framework.exceptions import ParseError
from rest_framework.parsers import JSONParser


class SafeJSONParser(JSONParser):
    """Recusa estruturas que excedem o limite de recursão do decodificador."""

    def parse(self, stream, media_type=None, parser_context=None):
        try:
            return super().parse(stream, media_type=media_type, parser_context=parser_context)
        except RecursionError:
            raise ParseError('JSON com profundidade excessiva. Simplifique a estrutura enviada.') from None
