"""
AI Tests - Testing the Cosmic Personality.

These tests verify Cosmic Eddie's rock personality works correctly.
Like a pre-show interview with the AI roadie!
"""

import pytest


class TestRockPersonality:
    """Tests for the rock personality system."""

    def test_personality_system_prompt(self):
        """Should generate a system prompt with rock personality."""
        from voice_handler.ai.prompts import RockPersonality

        personality = RockPersonality()
        prompt = personality.get_system_prompt()

        # Should contain rock references
        assert "Cosmic Eddie" in prompt or "roadie" in prompt.lower()
        assert "rock" in prompt.lower()

    def test_personality_tool_metaphors(self):
        """Should provide rock metaphors for tools."""
        from voice_handler.ai.prompts import RockPersonality

        personality = RockPersonality()

        # Test various tools
        read_metaphor = personality.get_tool_metaphor("Read")
        edit_metaphor = personality.get_tool_metaphor("Edit")
        bash_metaphor = personality.get_tool_metaphor("Bash")

        assert read_metaphor is not None
        assert edit_metaphor is not None
        assert bash_metaphor is not None

        # Unknown tool should have fallback
        unknown = personality.get_tool_metaphor("UnknownTool")
        assert unknown is not None

    def test_personality_acknowledgment_prompt(self):
        """Should generate acknowledgment prompts."""
        from voice_handler.ai.prompts import RockPersonality

        personality = RockPersonality()

        # With task description
        prompt_with_task = personality.get_acknowledgment_prompt(
            task_description="Write a function",
            user_nickname="TestUser"
        )
        assert "TestUser" in prompt_with_task
        assert "function" in prompt_with_task.lower() or "tarea" in prompt_with_task.lower()

        # Without task description
        prompt_without = personality.get_acknowledgment_prompt(
            task_description=None,
            user_nickname="Rockstar"
        )
        assert "Rockstar" in prompt_without

    def test_personality_completion_phrases(self):
        """Should provide completion phrases."""
        from voice_handler.ai.prompts import get_rock_personality

        personality = get_rock_personality()

        # Personality should have completion-related content
        prompt = personality.get_system_prompt()
        assert len(prompt) > 100  # Should have substantial content

    def test_personality_singleton(self):
        """Singleton should return same instance."""
        from voice_handler.ai.prompts import get_rock_personality

        p1 = get_rock_personality()
        p2 = get_rock_personality()

        assert p1 is p2


class TestQwenContextGenerator:
    """Tests for the Qwen context generator."""

    def test_qwen_initialization(self, mock_config, clean_singletons):
        """Qwen generator should initialize."""
        from voice_handler.ai.qwen import QwenContextGenerator

        qwen = QwenContextGenerator(config=mock_config)

        assert qwen.user_nickname == "TestRockstar"
        assert qwen.personality_style == "rockstar"

    def test_qwen_generates_greeting(self, mock_config, clean_singletons):
        """Should generate greetings (fallback if Qwen unavailable)."""
        from voice_handler.ai.qwen import QwenContextGenerator

        qwen = QwenContextGenerator(config=mock_config)

        # Even without Qwen, should return fallback
        greeting = qwen.generate_greeting(hour=10)

        assert greeting is not None
        assert len(greeting) > 0

    def test_qwen_generates_acknowledgment(self, mock_config, clean_singletons):
        """Should generate acknowledgments (fallback if Qwen unavailable)."""
        from voice_handler.ai.qwen import QwenContextGenerator

        qwen = QwenContextGenerator(config=mock_config)

        ack = qwen.generate_acknowledgment("Write a test function")

        assert ack is not None
        assert len(ack) > 0

    def test_qwen_generates_tool_announcement(self, mock_config, clean_singletons):
        """Should generate tool announcements."""
        from voice_handler.ai.qwen import QwenContextGenerator

        qwen = QwenContextGenerator(config=mock_config)

        announcement = qwen.generate_tool_announcement("Read", "/path/to/file.py")

        assert announcement is not None

    def test_qwen_generates_completion(self, mock_config, clean_singletons):
        """Should generate completion messages."""
        from voice_handler.ai.qwen import QwenContextGenerator

        qwen = QwenContextGenerator(config=mock_config)

        completion = qwen.generate_completion(
            summary="Fixed the bug",
            files_modified=3,
            commands_run=2
        )

        assert completion is not None

    def test_qwen_generates_approval_request(self, mock_config, clean_singletons):
        """Should generate approval requests."""
        from voice_handler.ai.qwen import QwenContextGenerator

        qwen = QwenContextGenerator(config=mock_config)

        request = qwen.generate_approval_request(tool_name="Edit")

        assert request is not None

    def test_qwen_generates_error_message(self, mock_config, clean_singletons):
        """Should generate error messages."""
        from voice_handler.ai.qwen import QwenContextGenerator

        qwen = QwenContextGenerator(config=mock_config)

        error = qwen.generate_error_message(error_details="Connection failed")

        assert error is not None

    def test_qwen_singleton(self, mock_config, clean_singletons):
        """Singleton should return same instance."""
        from voice_handler.ai.qwen import get_qwen_generator

        q1 = get_qwen_generator(config=mock_config)
        q2 = get_qwen_generator()

        assert q1 is q2
