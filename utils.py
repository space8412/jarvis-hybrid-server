import logging
import os
from typing import Dict, Any

# 로깅 설정
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

# 커스텀 예외 클래스들
class CustomError(Exception):
    pass

class APIError(CustomError):
    pass

class ValidationError(CustomError):
    pass

class EnvironmentError(CustomError):
    pass

# 환경 변수 검증
def validate_env_variables(required_vars: Dict[str, str]) -> None:
    missing = []
    for var, message in required_vars.items():
        if not os.getenv(var):
            missing.append(f"{var}: {message}")
    
    if missing:
        raise EnvironmentError("\n".join(missing))

# 비동기 HTTP 클라이언트
async def async_api_call(url: str, headers: dict, method: str = "GET", **kwargs) -> Any:
    import aiohttp
    async with aiohttp.ClientSession() as session:
        async with session.request(method, url, headers=headers, **kwargs) as response:
            if response.status != 200:
                raise APIError(f"API call failed: {await response.text()}")
            return await response.json() 