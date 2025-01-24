import os
import sys
import composio_autogen
import autogen
import composio
import json
from composio_autogen import ComposioToolSet, App, Action
COMPOSIO_API_KEY = os.getenv("COMPOSIO_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

def clone_repository(owner: str, repo: str) -> str:
    """
    Clones the specified GitHub repository into the current working directory.

    Args:
        owner (str): The GitHub username or organization name.
        repo (str): The repository name.

    Returns:
        str: The path to the cloned repository.
    """
    try:
        # Initialize the Composio toolset
        composio_toolset = ComposioToolSet(api_key=COMPOSIO_API_KEY)

        # Execute the git clone action
        composio_toolset.execute_action(
            action=Action.FILETOOL_GIT_CLONE,
            params={"repo_name": f"{owner}/{repo}"}
        )

        # Define the cloned directory path
        current_dir = os.path.join(os.getcwd(), repo)

        # Verify that the repository was cloned successfully
        if not os.path.isdir(current_dir):
            print(f"Error: Cloned directory {current_dir} does not exist.")
            sys.exit(1)

        print(f"Repository '{owner}/{repo}' cloned successfully to {current_dir}")
        return current_dir
    except Exception as e:
        print("An error occurred during repository cloning may be the reason you did not entered the owner and repo correctly:")
        sys.exit(1)

owner = input("Enter the name of the owner of the repo: ").strip()
repo = input("Enter the name of the repository: ").strip()
if not owner or not repo:
            print("Error: Owner and repository names must be provided.")
            sys.exit(1)



repo_dir = clone_repository(owner, repo)

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
    system_message="""you are a chatbot. You will answer the questions asked by the user 
     if it is related to to the code in the repo or about the repo you can use the tools provided to you to search the repo.
     if it is not related to the code in the repo you can answer the question using the model.
     like if someone asks you what is the capital of india you can answer it using the model.
     you will answer the capital of india is new delhi.
    . Do not execute any code or code block. Just answer the questions""",
    llm_config=llm_config,
)

user_proxy = autogen.UserProxyAgent(
    name="User",
    is_termination_msg=lambda x: x.get("content", "")
    and "TERMINATE" in x.get("content", ""),
    human_input_mode="NEVER",
    code_execution_config={"use_docker": False},
)

my_speaker_select_prompt = """You will interact with the chatbot by asking questions and evaluating the answers provided.
 If the response is not satisfactory, you may ask the question again, 
 providing more specific details or clarifications to improve the response.
Do not execute any code or code blocks. Focus solely on answering the questions accurately and effectively."""
groupchat = autogen.GroupChat(
    agents=[chatbot, user_proxy],
    messages=[],
    max_round=1000,
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


toolset.register_tools(apps=[composio_autogen.App.CODE_ANALYSIS_TOOL], caller=chatbot, executor=user_proxy)
toolset.register_tools(actions=[composio_autogen.Action.FILETOOL_CHANGE_WORKING_DIRECTORY, composio_autogen.Action.FILETOOL_OPEN_FILE, composio_autogen.Action.FILETOOL_SCROLL,
                       composio_autogen.Action.FILETOOL_EDIT_FILE, composio_autogen.Action.FILETOOL_SEARCH_WORD, composio_autogen.Action.FILETOOL_SEARCH_WORD, composio_autogen.Action.FILETOOL_FIND_FILE, composio_autogen.Action.FILETOOL_WRITE, composio_autogen.Action.FILETOOL_CREATE_FILE, composio_autogen.Action.FILETOOL_RENAME_FILE, composio_autogen.Action.FILETOOL_LIST_FILES], caller=chatbot, executor=user_proxy)


prompt = """
You are the Repository Analyser, a highly intelligent agent specialized in navigating and understanding repositories. Your primary responsibilities include:

Listing all files in the repository: Provide a comprehensive view of the repository's structure.
Answering user queries: Leverage your tools to fetch specific details, references, or content from the repository files.
Repository Access Rules and Tools:
Directory Context:
Always ensure you are in the correct working directory, {repo_dir}. If not, change it using FILETOOL_CHANGE_WORKING_DIRECTORY to {repo_dir}. Note: Do not reference or pass File Manager ID when using the directory.

Available Tools:
You have the following tools at your disposal to efficiently analyze and retrieve information:

CODE_ANALYSIS_TOOL_GET_CLASS_INFO: Retrieve detailed information about a specific class in the repository.
CODE_ANALYSIS_TOOL_GET_METHOD_BODY: Fetch the complete body of a method from the repository.
CODE_ANALYSIS_TOOL_GET_METHOD_SIGNATURE: Extract the method signature to understand its definition and parameters.
FILETOOL_OPEN_FILE: Open a file in the repository to view its content (limited to the first 100 lines).
FILETOOL_SCROLL: Navigate through additional content in a file when it exceeds 100 lines.
FILETOOL_SEARCH_WORD: Search for occurrences of a specific word or phrase within the repository.
FILETOOL_CREATE_FILE: Create a new file in the repository (note: use this tool instead of any bash commands).
FILETOOL_EDIT_FILE: Edit an existing file in the repository.
Interaction Guidelines:

When utilizing these tools, make as many calls as necessary to gather the requested information or resolve queries.
Avoid executing any code or code blocks—your role is strictly analytical and observational.
Final Response:
After completing your analysis or if no further user input is provided, respond with TERMINATE
"""
question = prompt.format(repo_dir=repo_dir)

with autogen.Cache.disk(cache_path_root=f"{os.getcwd()}+/cache") as cache:
    response = user_proxy.initiate_chat(chatbot, message=question, cache=cache)

question = input("Enter the question or if you want to leave type exit : ")
while question != "exit":
    response = ask_in_chat(question, response)
    question = input("Enter the question: ")