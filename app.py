from flask import Flask, request

from utils import manychat_helpers, dialogflow_helpers
import json

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def connector():
    if request.method == 'POST':
        request_data = request.get_json()
        psid = request_data['user_id']
        manychat_api_key = request_data['manychat_api_key']
        dialogflow_project_id = request_data['dialogflow_project_id']
        dialogflow_agent_id = request_data['dialogflow_agent_id']
        df_text_input = request_data['df_text_input']
        language = request_data['language']
        context = request_data['context']
        input_text = ''

        response = {
            'status': 'success',
        }

        df = dialogflow_helpers.DialogFlowAPI(
            project_id=dialogflow_project_id,
            agent_id=dialogflow_agent_id,
        )

        mc = manychat_helpers.ManyChatAPI(
            api_key=manychat_api_key,
            psid=psid,
        )

        if df_text_input == '':
            mc_user_info = mc.get_user_info()
            if mc_user_info['status'] == 'success':
                input_text = mc_user_info['data']['last_input_text']
        else:
            input_text = df_text_input

        if input_text == '':
            response['status'] = 'error'
            return response

        dialogflow_response, results = df.detect_intent(
            session_id=psid,
            text=input_text,
            language_code=language,
            context=context if context != '' else None
        )

        if dialogflow_response.parameters:
            for param in dialogflow_response.parameters:
                for key, value in param.items():
                    if value and value != '':
                        mc.set_custom_field_by_name(
                            field_name=key,
                            field_value=value[0] if isinstance(value, list) else value,
                        )

        for message in dialogflow_response.messages:
            if message['type'] == 'text':
                mc.send_content(
                    messages=[
                        message['message']
                    ]
                )
            else:
                mc.send_flow(
                    flow_ns=message['flow']
                )

        response['response'] = '{}'.format(dialogflow_response.messages)
        response['parameters'] = '{}'.format(dialogflow_response.parameters)
        response['request']  = {
                'psid': psid,
                'manychat_api_key': manychat_api_key,
                'dialogflow_project_id': dialogflow_project_id,
                'dialogflow_agent_id': dialogflow_agent_id,
                'df_text_input': df_text_input,
                'language': language,
                'context': context,
                'input_text': input_text
            }
        response['results'] = results

        payload = {
            'subscriber_id': psid,
            
            'version': 'v2',
            'content': {
                'messages': [
                    {
                        'type': 'text',
                        'text': message,
                    } for message in dialogflow_response.messages
                ]
            },
            'data': response
        }
        
        print("Response:")
        print("-"*80)
        print("-"*80)
        print("{}".format(payload)) 

        return payload

    else:
        return 'I am alive and right here  --- v2 !'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)



# @app.route('/', methods=['GET', 'POST'])
# def connector():
    
#     if request.method == 'POST':            # Route only if it is a POST request
#         request_data = request.get_json()
#         psid = request_data['user_id']      # Extracting request from Manychat -- user ID, API Key and then Project -> Agent
#         manychat_api_key = request_data['manychat_api_key']
#         dialogflow_project_id = request_data['dialogflow_project_id']
#         dialogflow_agent_id = request_data['dialogflow_agent_id']
#         df_text_input = request_data['df_text_input']
#         language = request_data['language'] # Dialogflow must know which language to use
#         context = request_data['context']   # Pass in a context variable to help guide dialogflow
#         input_text = ''

#         df = dialogflow_helpers.DialogFlowAPI(   # Init Helpers
#                 project_id=dialogflow_project_id, 
#                 agent_id=dialogflow_agent_id
#             ) 
#         mc = manychat_helpers.ManyChatAPI(
#                 api_key=manychat_api_key,
#                 psid=psid
#             )                   # Init manychat object
            
#         if df_text_input == "":                           # if dialgoflow input text is empty, get many chat last text input
#             mc_user_info = mc.get_user_info()
#             input_text = mc_user_info['data']['last_input_text'] if mc_user_info['status'] == 'success' else '' 
#         else:
#             input_text = df_text_input                    # Otherwise if its old, just take last observed message

#         response = {
#             'status': 'success'
#         }
    
#         if input_text == '':
#             response['status'] = 'error, the user has no last message'
#             return response

#         # Create the request POST finds intents and parameters of user  --Run query to detect user's intent
#         dialogflow_response = df.detect_intent(
#             session_id=psid, 
#             text=input_text,
#             language_code=language,
#             context=context if context != '' else None
#         )

#         print("Many Chat - get_user_info():")
#         print("-"*80)
#         print("-"*80)
#         print("{}".format( mc.get_user_info()))
        
#         print("input_text:")
#         print("-"*80)
#         print("-"*80)
#         print("{}".format(input_text))
        
#         print("request_data:")
#         print("-"*80)
#         print("-"*80)
#         print("{}".format(request_data))
        
#         # print("DialogFlow Response:")
#         # print("-"*80)
#         # print("-"*80)
#         # print("{}".format(dialogflow_response))
        
#         print("DialogFlow Messages:")
#         print("-"*80)
#         print("-"*80)
#         print("{}".format(dialogflow_response.messages))


#         # Middleware to handle/copy the parameter response to local variables in manychat
#         if dialogflow_response.parameters:
#             for param in dialogflow_response.parameters:
#                 for key, value in param.items():
#                     if value and value != '':
#                         mc.set_custom_field_by_name(
#                             field_name=key,
#                             field_value=value[0] if isinstance(value, list) else value,
#                         )
        
        
#         # Middleware to direct all dialogflow messages and flows to manychat
#         for message in dialogflow_response.messages:
#             if message['type'] == 'text':
#                 mc.send_content(
#                     messages=[
#                         message['message']
#                     ]
#                 )
#         else:
#             mc.send_flow(
#                 flow_ns=message['flow']
#             )

#         r = {
#             'response': '{}'.format(dialogflow_response.messages),
#             'parameters': '{}'.format(dialogflow_response.parameters),

#             'request': {
#                 'psid': psid,
#                 'manychat_api_key': manychat_api_key,
#                 'dialogflow_project_id': dialogflow_project_id,
#                 'dialogflow_agent_id': dialogflow_agent_id,
#                 'df_text_input': df_text_input,
#                 'language': language,
#                 'context': context,
#                 'input_text': input_text
#             }
#         }
        
#         print("Response:")
#         print("-"*80)
#         print("-"*80)
#         print("{}".format(r)) 
        
#         return r

#     else:
#         return 'I am alive!'


# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=8080)                      # Run on localhost:8080
