from flask import Flask, request

from utils import manychat_helpers, dialogflow_helpers
import json

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def connector():
    if request.method == 'POST':            # Route only if it is a POST request
        request_data = request.get_json()
        psid = request_data['user_id']      # Extracting request from Manychat -- user ID, API Key and then Project -> Agent
        manychat_api_key = request_data['manychat_api_key']
        dialogflow_project_id = request_data['dialogflow_project_id']
        dialogflow_agent_id = request_data['dialogflow_agent_id']
        df_text_input = request_data['df_text_input']
        language = request_data['language'] # Dialogflow must know which language to use
        context = request_data['context']   # Pass in a context variable to help guide dialogflow
        input_text = ''

        df = dialogflow_helpers.DialogFlowAPI(project_id=dialogflow_project_id, agent_id=dialogflow_agent_id) # Init a dialogflow object
        mc = manychat_helpers.ManyChatAPI(api_key=manychat_api_key, psid=psid)                   # Init manychat object
            
        if df_text_input == '':                           # if dialgoflow input text is empty, get many chat last text input
            mc_user_info = mc.get_user_info()
            input_text = mc_user_info['data']['last_input_text'] if mc_user_info['status'] == 'success' else '' 
        else:
            input_text = df_text_input                    # Otherwise if its old, just take last observed message

        response = {
            'status': 'success'
        }
    

        if input_text == '':
            response['status'] = 'error, the user has no last message'
            return response

        # Create the request POST finds intents and parameters of user  --Run query to detect user's intent
        dialogflow_response = df.detect_intent(
            session_id=psid, 
            text=input_text,
            language_code=language,
            context=context if context != '' else None
        )

        print('-'*40)
        print(json.dumps(dialogflow_response, indent=4, sort_keys=True))
        # print(json.dumps(dialogflow_response['parameters'], indent=4, sort_keys=True))
        print('-'*40)
    
    
        # Middleware to handle/copy the parameter response to local variables in manychat
        try:
            if dialogflow_response['parameters'] != {}:
                for param in dialogflow_response['parameters']:  
                    for key, value in param.items():          
                        if value and value != '':             
                            mc.set_custom_field_by_name(      
                                field_name=key,
                                field_value=value[0] if isinstance(value, list) else value, # Take the first value a list, otherwise value
                            )
        except:
            print(f"Parameters - No dialogflow response parameters in response")

        # Middleware to direct all dialogflow messages and flows to manychat
        try:
            for message in dialogflow_response['messages']:      
                if message['type'] == 'text':                 
                    mc.send_content(
                        messages=[
                            message['message']
                        ]
                    )
                else:                                         # Otherwise send a flow
                    mc.send_flow(
                        flow_ns = message['flow']
                    )
        except:
            print('Error - No return messages')

        
        # params   = dialogflow_response['parameters'].keys()
        # messages = dialogflow_response['messages'].keys()
        
        r = {
            'status': 'success',
            'dialogflow' : {
                'dialogflow_response': dialogflow_response,
                # 'dialogflow_parameters' : params,
                # 'dialogflow_messages'  : messages,
            },
            'data': {
                'psid': psid,
                'manychat_api_key': manychat_api_key,
                'dialogflow_project_id': dialogflow_project_id,
                'dialogflow_agent_id': dialogflow_agent_id,
                'df_text_input': df_text_input,
                'language': language,
                'context': context,
                'input_text': input_text
            }
        }

        return r

    else:
        return 'I am alive!'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)                      # Run on localhost:8080
