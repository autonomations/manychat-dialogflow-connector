import json
from dataclasses import dataclass

import requests


@dataclass
class DialogFlowAPI:   # Dialogflow API
    project_id: str    # Get the dialogflow project, agent, base
    agent_id: str
    base_url = 'https://dialogflow.cloud.google.com/v1/integrations/messenger/webhook'

    def detect_intent(self, 
                      session_id: str, 
                      text: str, 
                      language_code: str = 'en', 
                      context: str = None):
        
        response = lambda: None                        # Anonymous function to add infromation variables to
        response.messages = []
        response.parameters = []

        data = {
            'queryInput': {
                'text': {
                    'text': text,                      # Payload of TEXT
                    'languageCode': language_code,
                }
            },
        }

        if context:                                    # Add the context, if necessary
            data['queryParams'] = {
                'contexts': [
                    {
                        'name': f'projects/{self.project_id}/agent/sessions/{session_id}/contexts/{context}',
                        'lifespanCount': 1,
                    }
                ]
            }

        headerInfo = {'content-type': 'application/json' }
        df_response = requests.post(                   # Post to dialog flow webhook base / agent / session_id (manychat psid) / location
            url=f'{self.base_url}/{self.agent_id}/sessions/{session_id}?platform=webdemo',
            data=json.dumps(data),
            headers=headerInfo,
        )

        clean_response = df_response.text.replace(")]}'", "")   # Replace all )]}' for nothing
        results = json.loads(clean_response)
        # print(json.dumps(results, indent=4, sort_keys=True))


        if 'knowledgeAnswers' in results['queryResult']:
            if results['queryResult']['knowledgeAnswers']['answers']:
                response.messages.append(
                    {
                        'type': 'text',
                        'message': results['queryResult']['knowledgeAnswers']['answers'][0]['answer'],
                    }
                )

        
        if 'fulfillmentMessages' in results['queryResult']:
            for message in results['queryResult']['fulfillmentMessages']:  # Now that we already have our message
                if 'text' in message:
                    if message['text']['text'][0].startswith('flow:'):
                        response.messages.append(
                            {
                                'type': 'flow',
                                'flow': message['text']['text'][0].replace('flow:', '').strip()
                            }
                        )

                    else:
                        response.messages.append(
                            {
                                'type': 'text',
                                'message': message['text']['text'][0]
                            }
                        )

            
                elif 'payload' in message: 
                    if 'flow' in message['payload']:    
                        response.messages.append(           # keep the payload style for previous compatibility
                            {
                                'type': 'flow',
                                'flow': message['payload']['flow']
                            }
                        )

        if 'parameters' in results['queryResult']:          # copy the parameters 
            for key, value in results['queryResult']['parameters'].items():
                if key == 'date-period':
                    response.parameters += [
                        {
                            'startDate': value[0]['startDate']  
                        },
                        {
                            'endDate': value[0]['endDate']
                        }
                    ]

                else:
                    response.parameters.append(
                        {
                            key: value
                        }
                    )

        results['messages']   = response.messages  
        results['parameters'] = response.parameters
        
        return results
