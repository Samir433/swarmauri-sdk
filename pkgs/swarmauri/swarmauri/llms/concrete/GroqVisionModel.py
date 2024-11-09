import asyncio
import json
from pydantic import PrivateAttr
import httpx
import requests
from swarmauri.conversations.concrete.Conversation import Conversation
from typing import List, Optional, Dict, Literal, Any, AsyncGenerator, Generator

from swarmauri_core.typing import SubclassUnion
from swarmauri.messages.base.MessageBase import MessageBase
from swarmauri.messages.concrete.AgentMessage import AgentMessage
from swarmauri.llms.base.LLMBase import LLMBase

from swarmauri.messages.concrete.AgentMessage import UsageData


class GroqVisionModel(LLMBase):
    """
    GroqVisionModel class for interacting with the Groq vision language models API. This class
    provides synchronous and asynchronous methods to send conversation data to the
    model, receive predictions, and stream responses.

    Attributes:
        api_key (str): API key for authenticating requests to the Groq API.
        allowed_models (List[str]): List of allowed model names that can be used.
        name (str): The default model name to use for predictions.
        type (Literal["GroqModel"]): The type identifier for this class.


    Allowed Models resources: https://console.groq.com/docs/models
    """

    api_key: str
    allowed_models: List[str] = [
        "llama-3.2-11b-vision-preview",
    ]
    name: str = "llama-3.2-11b-vision-preview"
    type: Literal["GroqVisionModel"] = "GroqVisionModel"
    _api_url: str = PrivateAttr("https://api.groq.com/openai/v1/chat/completions")

    def _format_messages(
        self,
        messages: List[SubclassUnion[MessageBase]],
    ) -> List[Dict[str, Any]]:
        """
        Formats conversation messages into the structure expected by the API.

        Args:
            messages (List[MessageBase]): List of message objects from the conversation history.

        Returns:
            List[Dict[str, Any]]: List of formatted message dictionaries.
        """

        formatted_messages = []
        for message in messages:
            formatted_message = message.model_dump(
                include=["content", "role", "name"], exclude_none=True
            )

            if isinstance(formatted_message["content"], list):
                formatted_message["content"] = [
                    {"type": item["type"], **item}
                    for item in formatted_message["content"]
                ]

            formatted_messages.append(formatted_message)
        return formatted_messages

    def _prepare_usage_data(self, usage_data) -> UsageData:
        """
        Prepares and validates usage data received from the API response.

        Args:
            usage_data (dict): Raw usage data from the API response.

        Returns:
            UsageData: Validated usage data instance.
        """
        return UsageData.model_validate(usage_data)

    def _make_request(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sends a synchronous HTTP POST request to the API and retrieves the response.

        Args:
            data (dict): Payload data to be sent in the API request.

        Returns:
            dict: Parsed JSON response from the API.
        """
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        response = requests.post(self._api_url, headers=headers, json=data)
        response.raise_for_status()  # Raise an error for HTTP issues
        return response.json()

    def predict(
        self,
        conversation: Conversation,
        temperature: float = 0.7,
        max_tokens: int = 256,
        top_p: float = 1.0,
        enable_json: bool = False,
        stop: Optional[List[str]] = None,
    ) -> Conversation:
        """
        Generates a response from the model based on the given conversation.

        Args:
            conversation (Conversation): Conversation object with message history.
            temperature (float): Sampling temperature for response diversity.
            max_tokens (int): Maximum tokens for the model's response.
            top_p (float): Cumulative probability for nucleus sampling.
            enable_json (bool): Whether to format the response as JSON.
            stop (Optional[List[str]]): List of stop sequences for response termination.

        Returns:
            Conversation: Updated conversation with the model's response.
        """
        formatted_messages = self._format_messages(conversation.history)
        data = {
            "model": self.name,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "stop": stop or [],
        }
        if enable_json:
            data["response_format"] = "json_object"

        result = self._make_request(data)
        message_content = result["choices"][0]["message"]["content"]
        usage_data = result.get("usage", {})

        usage = self._prepare_usage_data(usage_data)
        conversation.add_message(AgentMessage(content=message_content, usage=usage))
        return conversation

    async def apredict(
        self,
        conversation: Conversation,
        temperature: float = 0.7,
        max_tokens: int = 256,
        top_p: float = 1.0,
        enable_json: bool = False,
        stop: Optional[List[str]] = None,
    ) -> Conversation:
        """
        Async method to generate a response from the model based on the given conversation.

        Args:
            conversation (Conversation): Conversation object with message history.
            temperature (float): Sampling temperature for response diversity.
            max_tokens (int): Maximum tokens for the model's response.
            top_p (float): Cumulative probability for nucleus sampling.
            enable_json (bool): Whether to format the response as JSON.
            stop (Optional[List[str]]): List of stop sequences for response termination.

        Returns:
            Conversation: Updated conversation with the model's response.
        """
        formatted_messages = self._format_messages(conversation.history)
        data = {
            "model": self.name,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "stop": stop or [],
        }
        if enable_json:
            data["response_format"] = "json_object"

        # Use asyncio's to_thread to call synchronous code in an async context
        result = await asyncio.to_thread(self._make_request, data)
        message_content = result["choices"][0]["message"]["content"]
        usage_data = result.get("usage", {})

        usage = self._prepare_usage_data(usage_data)
        conversation.add_message(AgentMessage(content=message_content, usage=usage))
        return conversation

    def stream(
        self,
        conversation: Conversation,
        temperature: float = 0.7,
        max_tokens: int = 256,
        top_p: float = 1.0,
        enable_json: bool = False,
        stop: Optional[List[str]] = None,
    ) -> Generator[str, None, None]:
        """
        Streams response text from the model in real-time.

        Args:
            conversation (Conversation): Conversation object with message history.
            temperature (float): Sampling temperature for response diversity.
            max_tokens (int): Maximum tokens for the model's response.
            top_p (float): Cumulative probability for nucleus sampling.
            enable_json (bool): Whether to format the response as JSON.
            stop (Optional[List[str]]): List of stop sequences for response termination.

        Yields:
            str: Partial response content from the model.
        """

        formatted_messages = self._format_messages(conversation.history)
        data = {
            "model": self.name,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "stream": True,
            "stop": stop or [],
        }
        if enable_json:
            data["response_format"] = "json_object"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        with requests.post(
            self._api_url, headers=headers, json=data, stream=True
        ) as response:
            response.raise_for_status()
            message_content = ""
            for line in response.iter_lines(decode_unicode=True):
                json_str = line.replace('data: ', '')
                try:
                    if json_str:
                        chunk = json.loads(json_str)
                        if chunk["choices"][0]["delta"]:
                            delta = chunk["choices"][0]["delta"]["content"]
                            message_content += delta
                            yield delta
                except json.JSONDecodeError:
                    pass

            conversation.add_message(AgentMessage(content=message_content))

    async def astream(
        self,
        conversation: Conversation,
        temperature: float = 0.7,
        max_tokens: int = 256,
        top_p: float = 1.0,
        enable_json: bool = False,
        stop: Optional[List[str]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Async generator that streams response text from the model in real-time.

        Args:
            conversation (Conversation): Conversation object with message history.
            temperature (float): Sampling temperature for response diversity.
            max_tokens (int): Maximum tokens for the model's response.
            top_p (float): Cumulative probability for nucleus sampling.
            enable_json (bool): Whether to format the response as JSON.
            stop (Optional[List[str]]): List of stop sequences for response termination.

        Yields:
            str: Partial response content from the model.
        """

        formatted_messages = self._format_messages(conversation.history)
        data = {
            "model": self.name,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
            "stream": True,
            "stop": stop or [],
        }
        if enable_json:
            data["response_format"] = "json_object"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(self._api_url, headers=headers, json=data, timeout=None)

            response.raise_for_status()
            message_content = ""
            async for line in response.aiter_lines():
                json_str = line.replace('data: ', '')
                try:
                    if json_str:
                        chunk = json.loads(json_str)
                        if chunk["choices"][0]["delta"]:
                            delta = chunk["choices"][0]["delta"]["content"]
                            message_content += delta
                            yield delta
                except json.JSONDecodeError:
                    pass

        conversation.add_message(AgentMessage(content=message_content))

    def batch(
        self,
        conversations: List[Conversation],
        temperature: float = 0.7,
        max_tokens: int = 256,
        top_p: float = 1.0,
        enable_json: bool = False,
        stop: Optional[List[str]] = None,
    ) -> List[Conversation]:
        """
        Processes a batch of conversations and generates responses for each sequentially.

        Args:
            conversations (List[Conversation]): List of conversations to process.
            temperature (float): Sampling temperature for response diversity.
            max_tokens (int): Maximum tokens for each response.
            top_p (float): Cumulative probability for nucleus sampling.
            enable_json (bool): Whether to format the response as JSON.
            stop (Optional[List[str]]): List of stop sequences for response termination.

        Returns:
            List[Conversation]: List of updated conversations with model responses.
        """
        results = []
        for conversation in conversations:
            result_conversation = self.predict(
                conversation,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p,
                enable_json=enable_json,
                stop=stop,
            )
            results.append(result_conversation)
        return results

    async def abatch(
        self,
        conversations: List[Conversation],
        temperature: float = 0.7,
        max_tokens: int = 256,
        top_p: float = 1.0,
        enable_json: bool = False,
        stop: Optional[List[str]] = None,
        max_concurrent=5,
    ) -> List[Conversation]:
        """
        Async method for processing a batch of conversations concurrently.

        Args:
            conversations (List[Conversation]): List of conversations to process.
            temperature (float): Sampling temperature for response diversity.
            max_tokens (int): Maximum tokens for each response.
            top_p (float): Cumulative probability for nucleus sampling.
            enable_json (bool): Whether to format the response as JSON.
            stop (Optional[List[str]]): List of stop sequences for response termination.
            max_concurrent (int): Maximum number of concurrent requests.

        Returns:
            List[Conversation]: List of updated conversations with model responses.
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_conversation(conv: Conversation) -> Conversation:
            async with semaphore:
                return await self.apredict(
                    conv,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=top_p,
                    enable_json=enable_json,
                    stop=stop,
                )

        tasks = [process_conversation(conv) for conv in conversations]
        return await asyncio.gather(*tasks)
