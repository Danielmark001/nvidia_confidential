"""
Medication Advisor LLM Agent using NVIDIA NIM and LangChain.
Implements function-calling agent with knowledge graph retrieval.
"""

from typing import List, Tuple, Any
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain.agents import AgentExecutor
from langchain.agents.format_scratchpad import format_to_openai_function_messages
from langchain.agents.output_parsers.openai_tools import OpenAIToolsAgentOutputParser
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema import AIMessage, HumanMessage
from pydantic import BaseModel, Field

from src.utils.config import config
from src.constants import AGENT_SYSTEM_PROMPT
from src.retrieval.tools import MEDICATION_TOOLS


class MedicationAdvisorAgent:
    """
    Medication advisor agent that answers questions about medications.

    Uses Llama 3.1 with function calling to retrieve information from
    a Neo4j knowledge graph containing discharge notes and DrugBank data.
    """

    def __init__(
        self,
        model: str = None,
        temperature: float = None,
        verbose: bool = True
    ):
        """
        Initialize the medication advisor agent.

        Args:
            model: NVIDIA NIM model name (defaults to config)
            temperature: LLM temperature (defaults to config)
            verbose: Whether to print agent steps
        """
        self.model_name = model or config.LLM_MODEL
        self.temperature = temperature if temperature is not None else config.LLM_TEMPERATURE
        self.verbose = verbose

        self.llm = self._initialize_llm()
        self.agent_executor = self._build_agent()

    def _initialize_llm(self) -> ChatNVIDIA:
        """Initialize the NVIDIA NIM LLM."""
        llm_kwargs = {
            "model": self.model_name,
            "temperature": self.temperature,
        }

        if config.LLM_BASE_URL:
            llm_kwargs["base_url"] = config.LLM_BASE_URL

        return ChatNVIDIA(**llm_kwargs)

    def _build_agent(self) -> AgentExecutor:
        """Build the LangChain agent with tools."""
        prompt = ChatPromptTemplate.from_messages([
            ("system", AGENT_SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        llm_with_tools = self.llm.bind_tools(tools=MEDICATION_TOOLS)

        agent = (
            {
                "input": lambda x: x["input"],
                "chat_history": lambda x: self._format_chat_history(x.get("chat_history", [])),
                "agent_scratchpad": lambda x: format_to_openai_function_messages(
                    x["intermediate_steps"]
                ),
            }
            | prompt
            | llm_with_tools
            | OpenAIToolsAgentOutputParser()
        )

        class AgentInput(BaseModel):
            input: str
            chat_history: List[Tuple[str, str]] = Field(default_factory=list)

        class Output(BaseModel):
            output: Any

        agent_executor = AgentExecutor(
            agent=agent,
            tools=MEDICATION_TOOLS,
            verbose=self.verbose,
            handle_parsing_errors=True,
            max_iterations=5
        ).with_types(
            input_type=AgentInput,
            output_type=Output
        )

        return agent_executor

    def _format_chat_history(self, chat_history: List[Tuple[str, str]]) -> List:
        """Format chat history for the agent."""
        buffer = []
        for human, ai in chat_history:
            buffer.append(HumanMessage(content=human))
            buffer.append(AIMessage(content=ai))
        return buffer

    def ask(self, question: str, chat_history: List[Tuple[str, str]] = None) -> str:
        """
        Ask the agent a question.

        Args:
            question: The user's question
            chat_history: Optional list of (human, ai) message tuples

        Returns:
            The agent's response
        """
        if chat_history is None:
            chat_history = []

        try:
            result = self.agent_executor.invoke({
                "input": question,
                "chat_history": chat_history
            })

            return result["output"]

        except Exception as e:
            return f"I encountered an error while processing your question: {str(e)}\nPlease try rephrasing your question or contact support if the issue persists."

    def chat(self):
        """
        Start an interactive chat session with the agent.
        """
        print("=" * 60)
        print("Medication Advisor - Interactive Chat")
        print("=" * 60)
        print("\nHello! I'm your medication advisor assistant.")
        print("I can help you with:")
        print("  - Medication dosages and schedules")
        print("  - Drug interactions")
        print("  - Medication information")
        print("  - Discharge instructions")
        print("\nType 'quit' or 'exit' to end the conversation.\n")
        print("=" * 60)

        chat_history = []

        while True:
            try:
                user_input = input("\nYou: ").strip()

                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\nThank you for using Medication Advisor. Take care!")
                    break

                if not user_input:
                    continue

                print("\nAgent:", end=" ", flush=True)

                response = self.ask(user_input, chat_history)

                print(response)

                chat_history.append((user_input, response))

                if len(chat_history) > 10:
                    chat_history = chat_history[-10:]

            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}")
                continue


def create_agent(verbose: bool = True) -> MedicationAdvisorAgent:
    """
    Factory function to create a medication advisor agent.

    Args:
        verbose: Whether to print agent steps

    Returns:
        Initialized MedicationAdvisorAgent
    """
    try:
        config.validate()
    except ValueError as e:
        print(f"Configuration error: {e}")
        print("\nPlease check your .env file and ensure all required values are set.")
        print("Copy .env.example to .env and fill in your API keys.")
        raise

    return MedicationAdvisorAgent(verbose=verbose)


if __name__ == "__main__":
    import sys

    print("Starting Medication Advisor Agent...")

    try:
        agent = create_agent(verbose=True)

        if len(sys.argv) > 1:
            question = " ".join(sys.argv[1:])
            print(f"\nQuestion: {question}")
            print(f"\nAnswer: {agent.ask(question)}")
        else:
            agent.chat()

    except Exception as e:
        print(f"\nFailed to start agent: {e}")
        sys.exit(1)
