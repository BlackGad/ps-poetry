# from typing import Iterable, Optional, Tuple

# from ps.token_expressions import ExpressionFactory
# from .models import Version, VersionStandard


# def split_condition(value: str) -> Tuple[Optional[str], str, bool]:
#     if value is None:
#         return None, "", False

#     text = value.strip()
#     if not text.startswith("["):
#         return None, text, True

#     end_index = text.find("]")
#     if end_index == -1:
#         return None, text, False

#     condition = text[1:end_index].strip()
#     remainder = text[end_index + 1:].strip()
#     if not condition:
#         return None, remainder or text, False

#     return condition, remainder, True


# def pick_version(inputs: Iterable[str], factory: ExpressionFactory) -> Version:
#     for input_value in inputs:
#         if input_value is None:
#             continue

#         condition, version_string, valid = split_condition(input_value)
#         if not valid:
#             continue

#         if condition is not None and not factory.match(condition):
#             continue

#         result = Version.parse(factory.materialize(version_string))
#         if result.standard != VersionStandard.UNKNOWN:
#             return result

#     return Version(major=0)
