
# for llamafile on First, run
#    ./llava-v1.5-7b-q4-server.llamafile
# 
# For WSL2, execute before running llamafile:
#    sudo sh -c 'echo :WSLInterop:M::MZ::/init:PF > /usr/lib/binfmt.d/WSLInterop.conf;
#    systemctl unmask systemd-binfmt.service;
#    systemctl restart systemd-binfmt;
#    systemctl mask systemd-binfmt.service;
#    echo -1 > /proc/sys/fs/binfmt_misc/WSLInterop'
#
# run webserver:
#    panel serve rtfm-ai.py --allow-websocket-origin=127.0.0.1:5006 &

import os
import openai
import panel as pn  # GUI
import sys

API = 'openai'

if (API == 'openai'):
    from dotenv import load_dotenv, find_dotenv
    _ = load_dotenv(find_dotenv())
    openai.api_key  = os.getenv('OPENAI_API_KEY')
    completion = openai.chat.completions
    model = 'gpt-3.5-turbo' # "This model's maximum context length is 4097 tokens
elif (API == 'llamafile'):
    client = openai.OpenAI(
        base_url="http://localhost:8080/v1", # "http://<Your api-server IP>:port"
        api_key = "sk-no-key-required"
    )
    completion = client.chat.completions
    model = 'LLaMA_CPP'

def get_completion(messages, model=model, temperature=0):
    response = completion.create(
        model=model,
        messages=messages,
        temperature=temperature
    )
    return response



from bs4 import BeautifulSoup
import re

def generate_file_dictionary(directory):
    file_dictionary = {}

    #print(f"Checking directory: {directory}")

    for root, dirs, files in os.walk(directory):

        for file_name in files:
            file_path = os.path.join(root, file_name)

            # Check if the file is binary
            if not is_binary(file_path):
                with open(file_path, 'r', encoding='utf-8') as file:
                    file_contents = file.read()
                    if file_path.endswith('.html') or file_path.endswith('.htm'):
                        soup = BeautifulSoup(file_contents, 'html.parser')
                        file_contents = soup.get_text()
                    
                    file_contents = re.sub('\n+', '\n', file_contents)
                    file_dictionary[file_path] = file_contents

    return file_dictionary

def is_binary(file_path):
    try:
        with open(file_path, 'rb') as f:
            content = f.read(1024)
            return b'\0' in content  # Binary files often contain null bytes
    except Exception as e:
        print(f"Error checking binary for {file_path}: {e}")
        return False

directory_path = '~/temp/controllability' # sys.argv[1] # INSERT YOUR DOC PATH

result_dict = generate_file_dictionary(os.path.expanduser(directory_path))
print(f"Files scanned: {len(result_dict)}")

print(result_dict)

#response = get_completion(messages)
# print only response text
#print(response.choices[0].message.content)
# print the whole ChatCompletionMessage object
#print(str(response.choices[0].message))


messages=[
    {"role": "system", "content": "You are an AI assistant, whose role it is to give detailed technical support to a software developer about a tool, library, or package"
     " from its documentation. Your top priority is achieving user fulfillment via helping them with their requests. "
     "In the following, you will see the contents of a number of text, HTML, PDF, and source code files of the tool, library, or package. "
     "Each file is separated by triple quotes and starts with the file name. The content starts on the next line."
     "Recall the file name and content sections from each file, such as headings or code functions, so you can include this information with your responses to point "
     "out where you found that information and quote it."
     "In your response, first give the name of the tool, library or package and one sentence summarizing its purpose. Then respond to user requests about the documention."
     },
    {"role": "assistant", "content": "First give the name of the tool, library or package and one sentence summarizing its purpose. "
     }
]

# Iterate over the generated dictionary
for path, content in result_dict.items():
    #print(f"File: {path}\nContents:\n{content}\n")
    messages[0]["content"] += f' \n\'\'\'{path}\n{content}\'\'\'\n'
    
#print(messages[0]["content"])

#response = get_completion(messages)
    



pn.extension()
inp = pn.widgets.TextInput(value="Hi", placeholder='Enter text here…')
button_conversation = pn.widgets.Button(name="Chat!")

panels = [] # collect display 
def collect_messages(_):
    prompt = inp.value_input
    inp.value = ''
    messages.append({'role':'user', 'content':f"{prompt}"})
    response = get_completion(messages)
    #response_content = response.choices[0].message['content']
    response_content = response.choices[0].message.content
    #response = get_completion(messages).choices[0].message
    messages.append({'role':'assistant', 'content':f"{response_content}"})
    panels.append(pn.Row('User:', pn.pane.Markdown(prompt, width=600)))
    panels.append(pn.Row('Assistant:', pn.pane.Markdown(response_content, width=600, style={'background-color': '#F6F6F6'})))
 
    return pn.Column(*panels)



interactive_conversation = pn.bind(collect_messages, button_conversation)

dashboard = pn.Column(
    inp,
    pn.Row(button_conversation),
    pn.panel(interactive_conversation, loading_indicator=True, height=300)
)

dashboard.servable()
