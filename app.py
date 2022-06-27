from flask import Flask, request

from utils import manychat_helpers, dialogflow_helpers
import json

app = Flask(__name__)


https://app.alpaca.markets/oauth/authorize?response_type=code&client_id=ba1aa93a99e8ae606452f8b512274b10&redirect_uri=https%3A%2F%2Fapi.stockbud.io%2Foauth%2Fcallback&scope=account%3Awrite%2Btrading%2Bdata&state=d2e2dQMJRhcRN9LUSOO6B9j0IeyuPS&mcp_token=eyJwaWQiOjEwNzAyOTEwMDk2MzQzMiwic2lkIjo1MjIwODI2MTkxMjYxNjUyLCJheCI6IjA4OWRkMDVhZjdkNjRjYTlhMjVmYjZhZDFiZDU3MmM2IiwidHMiOjE2NTYzMTkwNTIsImV4cCI6MTY1ODczODI1Mn0.9jzCcDocnydvnLu4tGm6H2h8HeUW2bz6YNX_EnxTipQ
https://app.alpaca.markets/oauth/authorize?response_type=code&client_id=ba1aa93a99e8ae606452f8b512274b10&redirect_uri=https%3A%2F%2Fapi.stockbud.io%2Foauth%2Fcallback&scope=account%3Awrite%20trading%20data&state=d2e2dQMJRhcRN9LUSOO6B9j0IeyuPS

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
            'request': request.get_json()
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

        dialogflow_response = df.detect_intent(
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
        # response['results'] = results

        messages = dialogflow_response.messages

        payload = {
            'subscriber_id': psid,
            
            'version': 'v2',
            'content': {
                'messages': [
                    {
                        'type': 'text',
                        'text': message,
                    } for message in messages
                ]
            }
          
        }
        
        response['manychat-payload'] = payload
        
    
        # print("Response:")
        # print("-"*80)
        # print("-"*80)
        # print("{}".format(payload)) 

        return response

    else:
        return 'I am alive and right here  --- v3 !'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
