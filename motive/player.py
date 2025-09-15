from typing import Optional, List, Dict, Any
import logging
import os
import time
import asyncio
from motive.llm_factory import create_llm_client
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from motive.character import Character


class Player:
    """
    Represents a single AI player, managing their LLM client,
    chat history, and logging, with performance optimizations.
    """

    def __init__(self, name: str, provider: str, model: str, log_dir: str, no_file_logging: bool = False):
        self.name = name
        self.llm_client = create_llm_client(provider, model)
        
        # Context management
        self.conversation_history = []  # Full history for logging
        self.recent_messages = []       # Active context (last 4-6 messages)
        self.conversation_summary = ""  # Summarized old history
        
        # Compatibility with existing GameMaster
        self.chat_history = self.conversation_history  # Alias for compatibility
        
        # Performance optimizations
        self.response_cache = {}        # Response caching
        self.max_context_messages = 6   # Reduced from unlimited
        self.summary_threshold = 8       # When to create summary
        self.max_response_length = 1000 # Max length for LLM responses
        
        self.log_dir = log_dir
        self.no_file_logging = no_file_logging
        self.logger = self._setup_logger()
        self.character: Optional[Character] = None # Link to Character instance

    def _setup_logger(self):
        """Sets up a dedicated logger for this player's chat history."""
        logger = logging.getLogger(self.name)
        logger.setLevel(logging.INFO)
        logger.propagate = False

        if not self.no_file_logging:
            player_log_file = os.path.join(self.log_dir, f"{self.name}_chat.log")
            handler = logging.FileHandler(player_log_file, mode="w", encoding="utf-8")
            formatter = logging.Formatter("%(asctime)s - %(message)s")
            handler.setFormatter(formatter)
            if not logger.handlers: # Avoid adding multiple handlers in tests
                logger.addHandler(handler)
        return logger

    def add_message(self, message: Any):
        """Adds a message to the player's full conversation history."""
        self.conversation_history.append(message)

    def _build_smart_context(self, new_human_message: HumanMessage) -> List[Any]:
        """
        Builds a smart context for the LLM, including system prompt,
        conversation summary, recent messages, and the new message.
        """
        context = []
        
        # Always include system prompt
        context.append(SystemMessage(content="You are a helpful assistant. Be concise and focused. Keep responses under 1000 characters."))
        
        # Add conversation summary if available
        if self.conversation_summary:
            context.append(HumanMessage(content=f"[Previous context: {self.conversation_summary}]"))
        
        # Add only recent messages (up to max_context_messages)
        # Ensure we don't add too many if summary is also present
        available_slots = self.max_context_messages - (2 if self.conversation_summary else 1) # System + (Summary)
        context.extend(self.recent_messages[-available_slots:])
        
        # Add the new message
        context.append(new_human_message)
        
        return context

    def _create_conversation_summary(self):
        """
        Summarizes older messages in recent_messages and updates conversation_summary.
        Keeps only the most recent messages.
        """
        if len(self.recent_messages) <= self.summary_threshold:
            return
        
        # Keep only the last few messages, summarize the rest
        messages_to_summarize = self.recent_messages[:-self.max_context_messages // 2] # Summarize older half
        self.recent_messages = self.recent_messages[-self.max_context_messages // 2:] # Keep newer half
        
        if messages_to_summarize:
            summary_parts = []
            for i, msg in enumerate(messages_to_summarize):
                if hasattr(msg, 'content') and msg.content:
                    # Take first 100 chars of content, add ellipsis if truncated
                    content_preview = msg.content[:100]
                    if len(msg.content) > 100:
                        content_preview += "..."
                    
                    if isinstance(msg, HumanMessage):
                        summary_parts.append(f"Human: {content_preview}")
                    elif isinstance(msg, AIMessage):
                        summary_parts.append(f"AI: {content_preview}")
            
            if summary_parts:
                new_summary = " | ".join(summary_parts)
                if self.conversation_summary:
                    self.conversation_summary += " | " + new_summary
                else:
                    self.conversation_summary = new_summary

    def _update_recent_messages(self, human_message: HumanMessage, ai_message: AIMessage):
        """Adds new messages to recent_messages and triggers summarization if needed."""
        self.recent_messages.append(human_message)
        self.recent_messages.append(ai_message)
        
        if len(self.recent_messages) > self.summary_threshold:
            self._create_conversation_summary()

    async def _send_message_with_retry(self, messages: List[Any], max_retries: int = 3) -> AIMessage:
        """Sends message to LLM with exponential backoff retry logic."""
        for attempt in range(max_retries + 1):
            try:
                response = await self.llm_client.ainvoke(messages)
                return AIMessage(content=response.content)
            except Exception as e:
                error_msg = str(e)
                if "timeout" in error_msg.lower() and attempt < max_retries:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    self.logger.warning(f"⚠️  LLM call timeout on attempt {attempt + 1}, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    self.logger.error(f"❌ LLM call failed after {attempt + 1} attempts: {error_msg}")
                    raise

    async def get_response_and_update_history(self, messages_for_llm: list) -> AIMessage:
        """
        Invokes the LLM client with smart context management, appends the AI's response
        to the player's chat history, and returns the response.
        
        This method maintains backward compatibility with the existing GameMaster interface
        while providing performance optimizations.
        """
        # Extract the human message from the messages_for_llm list
        # The GameMaster passes the full conversation history, but we only need the latest human message
        human_message = None
        for msg in reversed(messages_for_llm):
            if isinstance(msg, HumanMessage):
                human_message = msg
                break
        
        if human_message is None:
            # Fallback: create a human message from the last message content
            if messages_for_llm:
                last_msg = messages_for_llm[-1]
                if hasattr(last_msg, 'content'):
                    human_message = HumanMessage(content=last_msg.content)
                else:
                    human_message = HumanMessage(content=str(last_msg))
            else:
                human_message = HumanMessage(content="Continue the conversation.")
        
        # Check cache first
        cache_key = hash(human_message.content + str(self.recent_messages))
        if cache_key in self.response_cache:
            self.logger.info(f"🚀 Cache hit for {self.name}!")
            ai_response = self.response_cache[cache_key]
            self.add_message(human_message)
            self.add_message(ai_response)
            self._update_recent_messages(human_message, ai_response)
            return ai_response
        
        # Build smart context for LLM call
        messages_for_llm_optimized = self._build_smart_context(human_message)
        
        # Send message with retry logic
        ai_response = await self._send_message_with_retry(messages_for_llm_optimized)
        
        # Cache response
        self.response_cache[cache_key] = ai_response
        
        # Update histories
        self.add_message(human_message)
        self.add_message(ai_response)
        self._update_recent_messages(human_message, ai_response)
        
        return ai_response