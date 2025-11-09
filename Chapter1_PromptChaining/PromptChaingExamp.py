import os
from langchain_core.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from langchain_deepseek import ChatDeepSeek
from dotenv import load_dotenv

load_dotenv()

llm = ChatDeepSeek(
    model="deepseek-chat",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    # other params...
)

# messages = [
#     (
#         "system",
#         "You are a helpful assistant that translates English to French. Translate the user sentence.",
#     ),
#     ("human", "I love programming."),
# ]
# ai_msg = llm.invoke(messages)
# ai_msg.content
# print(ai_msg.content)

# prompt_template = PromptTemplate.from_template("What is {thing}?")
# llm_chain = prompt_template | llm
# result = llm_chain.invoke({"thing": "LCEL"})
# print(result.content)

# --- Prompt 1: Extract Information ---
prompt_extract = ChatPromptTemplate.from_template("Extract the technical specifications from the followingtext:\n\n{text_input}")
# --- Prompt 2: Transform to JSON ---
prompt_transform = ChatPromptTemplate.from_template("Transform the following specifications into a JSON object with'cpu', 'memory', and 'storage' as keys:\n\n{specifications}")
# --- Build the Chain using LCEL ---
# The StrOutputParser() converts the LLM's message output to a simple string.
extraction_chain = prompt_extract | llm | StrOutputParser()
# The full chain passes the output of the extraction chain into the 'specifications'
# variable for the transformation prompt.
full_chain = (
    {"specifications": extraction_chain}
    | prompt_transform
    | llm
    | StrOutputParser()
)
# --- Run the Chain ---
input_text = "The new laptop model features a 3.5 GHz octa-coreprocessor, 16GB of RAM, and a 1TB NVMe SSD."
# Execute the chain with the input text dictionary.
final_result = full_chain.invoke({"text_input": input_text})
print(final_result)
print("\n--- Final JSON Output ---")

