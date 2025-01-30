import os
import composio_autogen
import autogen
import composio
import json


COMPOSIO_API_KEY = os.getenv("COMPOSIO_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN", "")


repo_dir = input("Enter the directory path: ")

# if not os.path.exists(repo_dir):
#     print("Error: Directory does not exist.")
#     sys.exit(1)

# print("Directory exists.")

toolset = composio_autogen.ComposioToolSet(
    metadata={
        composio_autogen.App.CODE_ANALYSIS_TOOL: {
            "dir_to_index_path": repo_dir,
        },
        composio_autogen.App.FILETOOL: {
            "dir_to_index_path": repo_dir,
        }
    },
)

llm_config = {
    "config_list": [
        {
            "model": "gpt-4o",
            "temperature": 0.3,
        }
    ],
}



composio.ComposioToolSet().execute_action(
    action=composio.Action.CODE_ANALYSIS_TOOL_CREATE_CODE_MAP,
    params={},
    metadata={"dir_to_index_path": repo_dir}
)

chatbot = autogen.AssistantAgent(
    "chatbot",
    system_message="""you are a chatbot. You will answer the questions asked by the user. Do not execute any code or code block. Just answer the questions""",
    llm_config=llm_config,
)

user_proxy = autogen.UserProxyAgent(
    name="User",
    is_termination_msg=lambda x: x.get("content", "")
    and "TERMINATE" in x.get("content", ""),
    human_input_mode="NEVER",
    code_execution_config={"use_docker": False},
)

my_speaker_select_prompt = """
You'll ask a question to the chatbot and check the answer. 
If the answer isn't good enough, retry by adding specific details to improve the question.
Retry at most 4 times. If still unsatisfied, return the best available response.
Do not execute any code or code block. Just answer the questions.
"""

groupchat = autogen.GroupChat(
    agents=[chatbot, user_proxy],
    messages=[],
    max_round=20,
    select_speaker_prompt_template=my_speaker_select_prompt,
    speaker_selection_method="round_robin",
)

manager = autogen.GroupChatManager(
    groupchat=groupchat,
    llm_config=llm_config,
    is_termination_msg=lambda x: "TERMINATE" in x.get("content", ""),
)

def ask_in_chat(message, response):
    message_json = json.dumps(response.chat_history)
    manager.resume(messages=message_json, remove_termination_string="TERMINATE")
    with autogen.Cache.disk(cache_path_root=f"{os.getcwd()}+/cache") as cache:
        result = manager.initiate_chat(
            recipient=chatbot,
            message=message,
            clear_history=False,
            cache=cache
        )
    return result


# toolset.register_tools(apps=[composio_autogen.App.CODE_ANALYSIS_TOOL_GET_METHOD_BODY], caller=chatbot, executor=user_proxy)
toolset.register_tools(actions=[composio_autogen.Action.FILETOOL_CHANGE_WORKING_DIRECTORY, composio_autogen.Action.FILETOOL_OPEN_FILE, composio_autogen.Action.FILETOOL_SCROLL, composio_autogen.Action.FILETOOL_SEARCH_WORD, composio_autogen.Action.FILETOOL_FIND_FILE, composio_autogen.Action.FILETOOL_LIST_FILES, composio_autogen.Action.CODE_ANALYSIS_TOOL_GET_METHOD_BODY, composio_autogen.Action.CODE_ANALYSIS_TOOL_GET_CLASS_INFO, composio_autogen.Action.CODE_ANALYSIS_TOOL_GET_RELEVANT_CODE, composio_autogen.Action.CODE_ANALYSIS_TOOL_GET_METHOD_SIGNATURE], caller=chatbot, executor=user_proxy)


question = """
To answer questions, you can search for references and files within the specified That is {repo_dir} repository directory. Ensure that the working directory is set to `{repo_dir}` using `FILETOOL_CHANGE_WORKING_DIRECTORY` if it is not already set. This confines all file operations to the given directory.
You have access to the following tools to search the repo:
- `CODE_ANALYSIS_TOOL_GET_CLASS_INFO`: Fetch information about a class in the repository.
- `CODE_ANALYSIS_TOOL_GET_METHOD_BODY`: Fetch the body of a method in the repository.
- `CODE_ANALYSIS_TOOL_GET_METHOD_SIGNATURE`: Fetch the signature of a method in the repository.
- 'CODE_ANALYSIS_TOOL_GET_RELEVANT_CODE': Fetch the relevant code for a given query.
- `FILETOOL_OPEN_FILE`: Open a file in the repository and view the contents (only 100 lines are displayed at a time).
- `FILETOOL_SCROLL`: Scroll through a file in the repository.
- `FILETOOL_SEARCH_WORD`: Search for a word in the repository.
- `FILETOOL_FIND_FILE`: Find a file in the repository.


Remember: 
- This is an API service repository that would be running as a service.
- Identify the **main entry point** of the service and list all the APIs that can be called once the service is running.
- Start by Provide a structured summary of each API, including:
  - The API endpoint.
  - The HTTP method (e.g., GET, POST).
  - The parameters required to call it (if any).
  - The expected result/response format.

Call these functions as many times as needed to answer the question. When you are done or the user response is empty, reply TERMINATE.
"""

format_quesion = """
Question: {question}

You have access to the following tools to search the repo:
- `CODE_ANALYSIS_TOOL_GET_CLASS_INFO`: Fetch information about a class in the repository.
- `CODE_ANALYSIS_TOOL_GET_METHOD_BODY`: Fetch the body of a method in the repository.
- `CODE_ANALYSIS_TOOL_GET_METHOD_SIGNATURE`: Fetch the signature of a method in the repository.
- `FILETOOL_OPEN_FILE`: Open a file in the repository and view the contents (only 100 lines are displayed at a time).
- `FILETOOL_SCROLL`: Scroll through a file in the repository.
- `FILETOOL_SEARCH_WORD`: Search for a word in the repository.

Note: analyse the code do not execute any code block. Just answer the questions.
Call these functions as many times as needed to answer the question. And give very detailed and specific answer of the question When you are done or the user response is empty, reply TERMINATE.
"""

question = question.format(repo_dir=repo_dir)

with autogen.Cache.disk(cache_path_root=f"{os.getcwd()}+/cache") as cache:
    response = user_proxy.initiate_chat(chatbot, message=question, cache=cache)

question = input("Enter the question: ")

# question = input("Enter the question: ")
while question.lower() != "exit":
    if question.lower() == "file":
        with open("input.txt", "r") as file:
            question = file.read()
    question = format_quesion.format(question=question)
    response = ask_in_chat(question, response)
    question = input("Enter the question: ")