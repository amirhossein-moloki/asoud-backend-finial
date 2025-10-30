import os
import json
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class SMSCoreHandler:
    @staticmethod
    def _get_api_key() -> str:
        """Resolve API key from env or development settings mock."""
        env_key = os.environ.get('SMS_API')
        if env_key:
            return env_key
        # Development mock structure: settings.SMS_API = { 'API_KEY': 'development-key', ... }
        try:
            return getattr(settings, 'SMS_API', {}).get('API_KEY')  # type: ignore[arg-type]
        except Exception:
            return ''

    @staticmethod
    def _should_mock_send() -> bool:
        """Decide whether to short-circuit external SMS provider in dev/test."""
        if os.environ.get('SMS_DISABLE_SEND', '').lower() in ('1', 'true', 'yes'):
            return True
        api_key = SMSCoreHandler._get_api_key()
        # If no key or clearly a development key, mock the send
        return not api_key or api_key == 'development-key'
    @staticmethod
    def send_bulk(payload):
        if SMSCoreHandler._should_mock_send():
            logger.info("SMS bulk mocked (development): %s", json.dumps(payload, ensure_ascii=False))
            return {"status": 1, "message": "mocked", "data": None}

        headers = {
            'X-API-KEY': SMSCoreHandler._get_api_key(),
            'Content-Type': 'application/json'
        }
        URL = "https://api.sms.ir/v1/send/bulk"
        res = requests.post(URL, json=payload, headers=headers)
        return res.json()

    @staticmethod
    def send_pattern(payload):
        if SMSCoreHandler._should_mock_send():
            logger.info("SMS template mocked (development): %s", json.dumps(payload, ensure_ascii=False))
            return {"status": 1, "message": "mocked", "data": None}

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'text/plain',
            'x-api-key': SMSCoreHandler._get_api_key(),
        }
        URL = "https://api.sms.ir/v1/send/verify"
        res = requests.post(URL, json=payload, headers=headers)
        return res.json()

    @staticmethod
    def send_verification_code(mobile: str, code: str):
        # In development or when disabled, short-circuit and expose code for testing
        if SMSCoreHandler._should_mock_send():
            logger.info("SMS verify mocked (development) -> mobile=%s code=%s", mobile, code)
            return {"status": 1, "message": "mocked", "data": {"mobile": mobile, "code": code}}

        # Try template method first
        payload = {
            "mobile": mobile,
            "templateId": "260323",
            "parameters": [
                {
                    "name": "code",
                    "value": code
                }
            ]
        }

        headers = {
            'Content-Type': 'application/json',
            'Accept': 'text/plain',
            'x-api-key': SMSCoreHandler._get_api_key(),
        }

        URL = "https://api.sms.ir/v1/send/verify"
        res = requests.post(URL, json=payload, headers=headers)
        
        # If template fails, try simple bulk SMS as fallback
        result = res.json()
        if result.get('status') != 1:
            logger.warning(f"Template SMS failed: {result}, trying bulk SMS...")
            fallback_payload = {
                "lineNumber": "10008666",
                "messageText": f"کد تأیید آسود: {code}",
                "mobiles": [mobile],
                "sendDateTime": None
            }
            fallback_headers = {
                'X-API-KEY': SMSCoreHandler._get_api_key(),
                'Content-Type': 'application/json'
            }
            fallback_url = "https://api.sms.ir/v1/send/bulk"
            fallback_res = requests.post(fallback_url, json=fallback_payload, headers=fallback_headers)
            return fallback_res.json()
        
        return result
        


# example bulk payload:
# payload = {
#     "lineNumber": 300000000000,
#     "messageText": "Your Text",
#     "mobiles": [
#         "Your Mobile 1",
#         "Your Mobile 2"
#     ],
#     "sendDateTime": None
# }


# example pattern payload: 
# payload = {
#     "mobile": "Mobile",
#     "templateId": "templateID",
#     "parameters": [
#         {
#             "name": "PARAMETER1",
#             "value": "000000"
#         },
#         {
#             "name": "PARAMETER2",
#             "value": "000000"    
#         }
#     ]
# }


