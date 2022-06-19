from flask import Flask, request

from utils import manychat_helpers, dialogflow_helpers
import json

import logging
logging.basicConfig(filename="log.txt", level=logging.DEBUG)


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

        df = dialogflow_helpers.DialogFlowAPI(   # Init Helpers
                project_id=dialogflow_project_id, 
                agent_id=dialogflow_agent_id
            ) 
        mc = manychat_helpers.ManyChatAPI(
                api_key=manychat_api_key,
                psid=psid
            )                   # Init manychat object
            
        if df_text_input == "":                           # if dialgoflow input text is empty, get many chat last text input
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
        
        logging.debug('-'*80)
        logging.debug(msg=f'dialogflow_response: {json.dumps(dialogflow_response, indent=4, sort_keys=True)}')
        logging.debug('-'*80)
        
        # print('-'*40)
        # print(json.dumps(dialogflow_response['messages'], indent=4, sort_keys=True))
        # print('-'*40) 
    
        # Middleware to handle/copy the parameter response to local variables in manychat
        if dialogflow_response['parameters']:
            for key, value in enumerate(dialogflow_response['parameters']):  # for each of the parameters 
                    if value and value != '':             
                        mc.set_custom_field_by_name(      
                            field_name=key,
                            field_value=value[0] if isinstance(value, list) else value, # Take the first value a list, otherwise value
                        )
                        
                        logging.debug(msg=f"Get User Information:")
                        logging.debug('-'*80)
                        logging.debug('-'*80)
                        logging.debug(msg=f"{mc.get_user_info()}")
        
        # Middleware to direct all dialogflow messages and flows to manychat
        if dialogflow_response['messages']:
            for message in dialogflow_response['messages']:
                if message['type'] == 'text':
                    logging.debug(msg="-"*80)
                    logging.debug(msg="-"*80)
                    logging.debug(msg="Dialogflow TEXT -- {}".format(message['message']))
                    # print('message: {message}')           
                    mc.send_content(messages=[message['message']])
                else:                                                   # Otherwise send a flow
                    logging.debug(msg="-"*80)
                    logging.debug(msg="-"*80)
                    logging.debug(msg="Dialogflow FLOW  -- {}".format(message['flow']))
                    mc.send_flow(flow_ns = message['flow'])

    
        r = {
            'status': 'success',
            'dialogflow': {
                'dialogflow_response': dialogflow_response,
                'dialogflow_parameters' : dialogflow_response['queryResult']['parameters'],
                'dialogflow_messages'  : dialogflow_response['queryResult']['fulfillmentMessages'],
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
