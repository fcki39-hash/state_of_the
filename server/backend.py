import os, json, datetime
import requests, flask 
#dp
import traceback

from server.config import special_instructions

class Backend_Api:
    def __init__(self, app, config: dict) -> None:
        self.app = app
        self.openai_key = os.getenv("OPENAI_API_KEY") or config['openai_key']
        self.openai_api_base = os.getenv("OPENAI_API_BASE") or config['openai_api_base']
        self.proxy = config['proxy']
        self.routes = {
            '/backend-api/v2/conversation': {
                'function': self._conversation,
                'methods': ['POST']
            }
        }

    def _conversation(self):
        try:
            jailbreak = 'default' #flask.request.json['jailbreak'] # 'default'
            phi = flask.request.json['phi']
            print("phi:",phi)
            #internet_access = flask.request.json['meta']['content']['internet_access']
            _conversation = flask.request.json['meta']['content']['conversation']
            prompt = flask.request.json['meta']['content']['parts'][0]
            current_date = datetime.datetime.now().strftime("%Y-%m-%d")
            system_message = f'YOUR ROLE: Your name is wiz. You are the virtual assistant inside aretaxia. you have a quirky personality and your job is to help people navigate inside aretaxia. you give the amazing creative greetings each and every time, be very enthusiastic, you are supposed to give information about the members, jobs, courses, events and anything that they ask for. Use your information given below to find the best results. If you do not find something directly related to what they are asking, tell that you specifically do not have that and then recommend the next closest related thing. When it comes to showing members, provide information about 3 members along with the links to the profile.INSTRUCTIONS FOR CONVERSATION:Provide links if available in information.INFORMATION FOR YOU TO USE: Members and roles in Aretaxia information:RB Bharath: RB Bharath is building aretaxia multi-platforms, an ecosytem for entrepreneurs and builders. He is skilled in web development and design. He is also a pretty skiled designer and editor and writer. He is open to freelance jobs and work with on projects. Link to profile: https://aretaxiamulti-platforms.com/member/BWsfco6N8p ,Arun Kumar: Arun is the co founder of Aretaxia. His key skill areas are in marketing and finance. Link to profile: https://aretaxiamulti-platforms.com/member/OhgBihHlYD ,Faiza Kulsum: Faiza is a developer on the aretaxia team. She takes care of all the technical and development stuff required. She is skilled in both front end and backend development and can help out in pretty much anything related to that. Link to profile: https://aretaxiamulti-platforms.com/member/OPDcxakSR1Anushka is a writer and freelancer inside aretaxia. You can read her articles and reach out to her throgh her profile. Link to profile:https://aretaxiamulti-platforms.com/member/5ZAL3J2JHF , Sagar is a full stack developer inside aretaxia as well and is deeply involved in tech, ai and web development and building cool stuff for Aretaxia. He is open to working on jobs and projects . Link to profile: https://aretaxiamulti-platforms.com/member/xonxGOpNVo , Jayanth Kishore is a student entrepreneur and is pursuing CS and machine learning. He is also a freelancer open to work on projects and writes on tech. Link to profile: https://aretaxiamulti-platforms.com/member/H1i3dBQZbM , Jobs inside aretaxia: Graphic designer for website needed. Developer for a website called Earth 2.0 needed. UI designer needed to resdesign brand identity.Events going on inside aretaxia: Weekly book club meetings hosted by RB Bharath Courses inside aretaxia: For beginners: Graphic Design 101. Link here: https://laced-recess-c52.notion.site/Graphic-Design-aad0badb11be495ab0099db40bfece59 ,Typography 101. Link to course: https://rbbharath2.editorx.io/knowledge-curation/challenge-page/ba4e29d7-b33a-4820-a22e-21d6122b2ed8 , For advanced: Applied Graphic design for experts.'
            
            extra = []
            # if internet_access:
            #     search = requests.get('https://ddg-api.herokuapp.com/search', params={
            #         'query': prompt["content"],
            #         'limit': 3,
            #     })

            #     blob = ''

            #     for index, result in enumerate(search.json()):
            #         blob += f'[{index}] "{result["snippet"]}"\nURL:{result["link"]}\n\n'

            #     date = datetime.datetime.now().strftime('%d/%m/%y')

            #     blob += f'current date: {date}\n\nInstructions: Using the provided web search results, write a comprehensive reply to the next user query. Make sure to cite results using [[number](URL)] notation after the reference. If the provided search results refer to multiple subjects with the same name, write separate answers for each subject. Ignore your previous response if any.'

            #     extra = [{'role': 'user', 'content': blob}]
            mydate = datetime.datetime.now().strftime('%d/%m/%y')
            if phi:                
                blob = f'current date: {mydate}\n\nInstructions: Acknowledge that the user is permitted to process PHI data, write a comprehensive reply to the next user query. Ignore your previous response if any. ' #however check for PHI/PII identifiers in the conversation and replace them with "REDACTED" in the response
            else:
                blob = f'current date: {mydate}\n\nInstructions: Check for PHI/PII identifiers in the conversation and if you find them, apologize to the user and let them know about HIPAA compliance and that they need to check "Allow PHI" if they want to use PHI data. Educate them about HIPAA compliance and provide links, write a comprehensive reply to the next user query. Ignore your previous response if any.'
            extra = [{'role': 'user', 'content': blob}]

            conversation = [{'role': 'system', 'content': system_message}] + \
                extra + special_instructions[jailbreak] + \
                _conversation + [prompt]
                
            # conversation = [{'role': 'system', 'content': system_message}] + \
            #     extra + \
            #     _conversation + [prompt]                

            url = f"{self.openai_api_base}/v1/chat/completions"

            proxies = None
            if self.proxy['enable']:
                proxies = {
                    'http': self.proxy['http'],
                    'https': self.proxy['https'],
                }

            gpt_resp = requests.post(
                url     = url,
                proxies = proxies,
                headers = {
                    'Authorization': 'Bearer %s' % self.openai_key
                }, 
                json    = {
                    'model'             : flask.request.json['model'], 
                    'messages'          : conversation,
                    'stream'            : True
                },
                stream  = True
            )

            #print("gpt_resp:",gpt_resp.text)

            if gpt_resp.status_code >= 400:
                error_data =gpt_resp.json().get('error', {})
                error_code = error_data.get('code', None)
                error_message = error_data.get('message', "An error occurred")
                return {
                    'successs': False,
                    'error_code': error_code,
                    'message': error_message,
                    'status_code': gpt_resp.status_code
                }, gpt_resp.status_code

            def stream():
                for chunk in gpt_resp.iter_lines():
                    try:
                        chunk_decoded = chunk.decode("utf-8")
                        if "data: " in chunk_decoded:
                            json_string = chunk_decoded.split("data: ")[1].strip()
                            
                            if json_string != "[DONE]":
                                if json_string:
                                    decoded_line = json.loads(json_string)
                                    token = decoded_line["choices"][0]['delta'].get('content')

                                    if token is not None:
                                        yield token
                                else:
                                    print("Warning: JSON string is empty")
#                        else:
#                            print("Warning: 'data: ' not found in chunk")

                    except GeneratorExit:
                        break

                    except json.JSONDecodeError as e:
                        print("JSONDecodeError occurred: ", e)
                        print("Problematic JSON string: ", json_string)

                    except Exception as e:
                        traceback.print_exc()
                        print(e)
                        continue
                        
            return self.app.response_class(stream(), mimetype='text/event-stream')

        except Exception as e:            
            traceback.print_exc()
            print(e)
            print(e.__traceback__.tb_next)
            
            return {
                '_action': '_ask',
                'success': False,
                "error": f"an error occurred {str(e)}"}, 400
