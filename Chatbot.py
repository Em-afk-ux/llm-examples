import openai
import streamlit as st
import requests
import openai, os, requests

openai.api_type = "azure"

# Azure OpenAI on your own data is only supported by the 2023-08-01-preview API version
openai.api_version = "2023-08-01-preview"

# Azure OpenAI setup
openai.api_base = "https://frendetestopenai.openai.azure.com/" # Add your endpoint here
openai.api_key = "fb2a7f4cc9bd4d8ab067871ee72aa90c" # Add your OpenAI API key here
deployment_id = "TestFrendePGT35Turbo" # Add your deployment ID here
# Azure Cognitive Search setup
search_endpoint = "https://frendetestopenaisearch2gb.search.windows.net"; # Add your Azure Cognitive Search endpoint here
search_key = "dZP52jK2Uiv45FVEjccVqivB5anttdfzrnVv7Vd3zwAzSeAUWvP4"; # Add your Azure Cognitive Search admin key here
search_index_name = "haandbok-ingen-tall"; # Add your Azure Cognitive Search index name here

def setup_byod(deployment_id: str) -> None:
    """Sets up the OpenAI Python SDK to use your own data for the chat endpoint.

    :param deployment_id: The deployment ID for the model to use with your own data.

    To remove this configuration, simply set openai.requestssession to None.
    """

    class BringYourOwnDataAdapter(requests.adapters.HTTPAdapter):

        def send(self, request, **kwargs):
            request.url = f"{openai.api_base}/openai/deployments/{deployment_id}/extensions/chat/completions?api-version={openai.api_version}"
            return super().send(request, **kwargs)

    session = requests.Session()

    # Mount a custom adapter which will use the extensions endpoint for any call using the given `deployment_id`
    session.mount(
        prefix=f"{openai.api_base}/openai/deployments/{deployment_id}",
        adapter=BringYourOwnDataAdapter()
    )

    openai.requestssession = session

setup_byod(deployment_id)
#Er egentlig system message nødvendig? "role": "system", "content": "Du er en AI assistent som skal svare Frende-ansatte på spørsmål basert på innholdet i personalhåndboken. Du må oppgi relevante linker til hvor man kan lese mer om temaet du oppgir i svaret. Svaret skal være på norsk. Dersom det ikke finnes i personalhåndboken skal du nekte å svare. Dersom input består av enkeltord så skal svaret være \\\"Vennligst skriv en litt mer utfyllende beskrivelse av det du ønsker å få svar på."}
#Bruker roleinformation istedet
def get_answer(userQuery):
    completion = openai.ChatCompletion.create(
        messages=[{"role": "system", "content": "Alle svar skal være utfyllende."},{"role": "user", "content": userQuery}],
        deployment_id=deployment_id,
        temperature=0.5,
        max_tokens=1500,
        top_p=0.2,
        frequency_penalty=0,
        presence_penalty=0,
        dataSources=[  # camelCase is intentional, as this is the format the API expects
            {
                "type": "AzureCognitiveSearch",
                "parameters": {
                    "endpoint": search_endpoint,
                    "key": search_key,
                    "indexName": search_index_name,
                    "queryType": "simple",
                    "roleInformation": """Du er en AI assistent som skal svare Frende-ansatte på spørsmål basert på innholdet i 
                    personalhåndboken. Du må oppgi relevante linker til hvor man kan lese mer om temaet du oppgir i svaret. 
                    Svaret skal være på norsk. Dersom det ikke finnes i personalhåndboken skal du nekte å svare. Alle svar skal være utfyllende, minst to setninger.
                    Dersom input består av enkeltord så skal svaret være 
                    \\\"Vennligst skriv en litt mer utfyllende beskrivelse av det du ønsker å få svar på. I svaret skal du ha et avsnitt som er kopiert fra dokumentet som er relevant til spørsmålet.""",

                    "inScope": True
                }
            }
        ]
    )
    return completion

st.title("Hr Chatbot")
st.caption("Hr Chat")
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state["messages"]:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    st.session_state["messages"].append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)
    
    response = get_answer(st.session_state.messages)
    msg = response["choices"][0]["message"]["content"]
    st.session_state["messages"].append(msg)
    st.chat_message("assistant").write(msg.content)
