from __future__ import annotations

import pytest

from ai_sdr_platform.src.agents.conversation.classifier import (
    ComplianceGuardrailClassifier,
    SafeFallbackClassifier,
)
from ai_sdr_platform.src.agents.outreach.models import OutreachMessage
from ai_sdr_platform.src.agents.outreach.providers import (
    ResendEmailProvider,
    TwilioMessagingProvider,
)
from ai_sdr_platform.src.infra.llm.client import MultiProviderLLMClient
from ai_sdr_platform.src.shared.config import settings


def test_resend_email_provider_initialization_and_test_redirect():
    provider = ResendEmailProvider(
        api_key="re_test_12345",
        from_email="onboarding@resend.dev",
        sender_name="SDR Test Team",
        test_recipient="dev.test@sdr.local",
    )
    assert provider.name == "resend"
    assert provider.api_key == "re_test_12345"
    assert provider.test_recipient == "dev.test@sdr.local"


def test_twilio_messaging_provider_initialization():
    sms = TwilioMessagingProvider(
        account_sid="AC12345",
        auth_token="token123",
        from_number="+15550001111",
        channel="sms",
    )
    assert sms.name == "twilio"
    assert sms.channel == "sms"

    whatsapp = TwilioMessagingProvider(
        account_sid="AC12345",
        auth_token="token123",
        from_number="+15550001111",
        channel="whatsapp",
    )
    assert whatsapp.channel == "whatsapp"


def test_enhanced_compliance_guardrail_classifier():
    classifier = ComplianceGuardrailClassifier()

    # Test migrated keyword "opt-out"
    res1 = classifier.classify("Please opt-out my email from future sends")
    assert res1 is not None
    assert res1.intent == "unsubscribe"
    assert res1.confidence == 0.98

    # Test migrated keyword "doesn't handle"
    res2 = classifier.classify("I doesn't handle sales inquiries here")
    assert res2 is not None
    assert res2.intent == "wrong_person"
    assert res2.confidence == 0.94

    # Test migrated keyword "ooo"
    res3 = classifier.classify("Currently ooo until next week")
    assert res3 is not None
    assert res3.intent == "out_of_office"
    assert res3.confidence == 0.94


def test_enhanced_safe_fallback_classifier():
    classifier = SafeFallbackClassifier()

    # Single match test (baseline 0.68 confidence preserved)
    res1 = classifier.classify("how much for 10 seats?")
    assert res1.intent == "pricing_request"
    assert res1.confidence == 0.68

    # Multi-term match test (dynamic scoring boost)
    res2 = classifier.classify("Let's talk, sounds good sounds great to connect!")
    assert res2.intent == "interested"
    assert res2.confidence > 0.68
    assert res2.confidence <= 0.95


def test_multi_provider_llm_client_routing():
    # Test Groq key smart routing (gsk_ prefix)
    client1 = MultiProviderLLMClient(grok_api_key="gsk_1234567890abcdef")
    assert client1.provider_name == "Groq LLM"
    assert client1.api_url == "https://api.groq.com/openai/v1/chat/completions"

    # Test xAI Grok key
    client2 = MultiProviderLLMClient(grok_api_key="xai_abcdef123456")
    assert client2.provider_name == "xAI Grok"
    assert client2.api_url == "https://api.x.ai/v1/chat/completions"

    # Test Ollama fallback
    client3 = MultiProviderLLMClient(grok_api_key="", groq_api_key="")
    assert client3.provider_name == "Ollama Local"
