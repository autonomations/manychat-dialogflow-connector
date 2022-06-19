import json
from dataclasses import dataclass, field
from typing import Union

import requests


@dataclass
class ManyChatAPI:
    api_base_url = 'https://api.manychat.com/fb/'     # Initialize API - base_url, key, id, headers
    api_key: str
    psid: str
    headers: dict = field(init=False)

    def __post_init__(self):                         # Headers that authenticate Manychat App for trust
        self.headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
        }

    def get_user_info(self) -> dict:                 
        params = {                                  # Get the user information
            'subscriber_id': self.psid,             # Set the ID number
        }

        try:
            response = requests.get(                 # Get info of user request
                url=f'{self.api_base_url}subscriber/getInfo',
                headers=self.headers,
                params=params,
                timeout=5,
            )
        except Exception as e:                
            results = {                             # If it fails... throw an error
                'status': 'error',
                'message': e,
            }
        else:       
            results = json.loads(response.text)   # If everything goes well, return user info

        return results

    def send_content(self, messages: list) -> dict:
        params = {                                # Method to send a message back to Manychat
            'subscriber_id': self.psid,
            'data': {
                'version': 'v2',                  # Compatible with Manychat
                'content': {
                    'messages': [
                        {
                            'type': 'text',
                            'text': message,
                        } for message in messages    # Shorthand for handling all messages
                    ]
                }
            },
        }

        try:
            response = requests.post(
                url=f'{self.api_base_url}sending/sendContent',
                headers=self.headers,
                data=json.dumps(params),
                timeout=5,
            )
        except Exception as e:
            results = {
                'status': 'error',
                'message': e,
            }
        else:
            results = json.loads(response.text)

        return results

    def send_flow(self, flow_ns: str) -> dict:
        params = {
            'subscriber_id': self.psid,
            'flow_ns': flow_ns,
        }

        try:
            response = requests.post(
                url=f'{self.api_base_url}sending/sendFlow',
                headers=self.headers,
                data=json.dumps(params),
                timeout=5,
            )
        except Exception as e:
            results = {
                'status': 'error',
                'message': e,
            }
        else:
            results = json.loads(response.text)

        return results

    def set_custom_field_by_name(self,
                                 field_name: str,
                                 field_value: Union[str, int, bool]) -> dict:
        params = {
            'subscriber_id': self.psid,
            'field_name': field_name,
            'field_value': field_value,
        }

        try:
            response = requests.post(
                url=f'{self.api_base_url}subscriber/setCustomFieldByName',
                headers=self.headers,
                data=json.dumps(params),
                timeout=5,
            )
        except Exception as e:
            results = {
                'status': 'error',
                'message': e,
            }
        else:
            results = json.loads(response.text)

        return results
