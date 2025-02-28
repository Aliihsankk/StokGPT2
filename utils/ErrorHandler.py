from typing import Any, Optional

class ErrorHandler:
    @staticmethod
    def handle_operation(operation: callable, *args, **kwargs) -> tuple[bool, Optional[Any], Optional[str]]:
        try:
            result = operation(*args, **kwargs)
            return True, result, None
        except Exception as e:
            return False, None, str(e)

    @staticmethod
    def validate_input(value: Any, expected_type: type, field_name: str) -> Optional[str]:
        if not isinstance(value, expected_type):
            return f"{field_name} geçersiz tip: {type(value).__name__}, beklenen: {expected_type.__name__}"
        return None
