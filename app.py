from flask import Flask, request

from utils import manychat_helpers, dialogflow_helpers

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

        response = {
            'status': 'success',
        }

        df = dialogflow_helpers.DialogFlowAPI(  # Init a dialogflow object
            project_id=dialogflow_project_id,
            agent_id=dialogflow_agent_id,
        )

        mc = manychat_helpers.ManyChatAPI(     # Init manychat object
            api_key=manychat_api_key,
            psid=psid,
        )

        if df_text_input == '':                 # if dialgoflow input text is empty, get many chat last text input
            mc_user_info = mc.get_user_info()
            if mc_user_info['status'] == 'success':
                input_text = mc_user_info['data']['last_input_text']  # Get last text
        else:
            input_text = df_text_input   # Otherwise if its old, just take last observed message

        if input_text == '':
            response['status'] = 'error'
            return response

        dialogflow_response = df.detect_intent(     # Using the agent and what it knows...
            session_id=psid,                        # Run query to detect user's intent
            text=input_text,
            language_code=language,
            context=context if context != '' else None
        )

        if dialogflow_response.parameters:                # If there are parameters...
            for param in dialogflow_response.parameters:  # then for each parameter
                for key, value in param.items():          # extract the entity and entity value
                    if value and value != '':             # If its not empty
                        mc.set_custom_field_by_name(      # Set the manychat custom field entity
                            field_name=key,
                            field_value=value[0] if isinstance(value, list) else value, # Take the first value a list, otherwise value
                        )

        for message in dialogflow_response.messages:   # for each message
            if message['type'] == 'text':              # if type text, send message
                mc.send_content(
                    messages=[
                        message['message']
                    ]
                )
            else:                                       # Otherwise send to flow
                mc.send_flow(
                    flow_ns = message['flow']
                )

        return response

    else:
        return 'I am alive!'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)   # Run on localhost:8080
