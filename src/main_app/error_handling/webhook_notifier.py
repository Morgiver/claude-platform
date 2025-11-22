"""Webhook notifier for critical error notifications."""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime
import httpx


logger = logging.getLogger(__name__)


class WebhookNotifier:
    """
    Sends webhook notifications for critical errors.

    Supports async HTTP POST requests to configured webhook URLs.
    Commonly used for Slack, Discord, or custom monitoring systems.
    """

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        timeout: float = 10.0,
        enabled: bool = True,
    ) -> None:
        """
        Initialize webhook notifier.

        Args:
            webhook_url: URL to send webhooks to
            timeout: Request timeout in seconds
            enabled: Enable/disable notifications
        """
        self.webhook_url = webhook_url
        self.timeout = timeout
        self.enabled = enabled and webhook_url is not None

        if self.enabled:
            logger.info(f"WebhookNotifier initialized (URL: {webhook_url})")
        else:
            logger.info("WebhookNotifier disabled (no URL configured)")

    async def notify_error(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        severity: str = "error",
    ) -> bool:
        """
        Send error notification via webhook.

        Args:
            error: Exception that occurred
            context: Additional context about the error
            severity: Severity level (error, critical, warning)

        Returns:
            True if notification sent successfully
        """
        if not self.enabled:
            logger.debug("Webhook notifications disabled, skipping")
            return False

        try:
            payload = self._build_payload(error, context, severity)
            return await self._send_webhook(payload)
        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}", exc_info=True)
            return False

    def notify_error_sync(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        severity: str = "error",
    ) -> bool:
        """
        Synchronous version of notify_error.

        Args:
            error: Exception that occurred
            context: Additional context about the error
            severity: Severity level

        Returns:
            True if notification sent successfully
        """
        try:
            return asyncio.run(self.notify_error(error, context, severity))
        except Exception as e:
            logger.error(f"Failed to send sync webhook notification: {e}", exc_info=True)
            return False

    def _build_payload(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]],
        severity: str,
    ) -> Dict[str, Any]:
        """
        Build webhook payload.

        Args:
            error: Exception
            context: Additional context
            severity: Severity level

        Returns:
            Payload dict
        """
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "severity": severity,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {},
        }

        return payload

    async def _send_webhook(self, payload: Dict[str, Any]) -> bool:
        """
        Send webhook HTTP POST request.

        Args:
            payload: JSON payload to send

        Returns:
            True if request successful
        """
        if not self.webhook_url:
            return False

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    self.webhook_url,
                    json=payload,
                )
                response.raise_for_status()

                logger.info(
                    f"Webhook notification sent successfully: {payload['error_type']}"
                )
                return True

        except httpx.HTTPError as e:
            logger.error(f"Webhook HTTP error: {e}", exc_info=True)
            return False

    def set_webhook_url(self, url: str) -> None:
        """
        Update webhook URL.

        Args:
            url: New webhook URL
        """
        self.webhook_url = url
        self.enabled = url is not None
        logger.info(f"Webhook URL updated: {url}")

    def disable(self) -> None:
        """Disable webhook notifications."""
        self.enabled = False
        logger.info("Webhook notifications disabled")

    def enable(self) -> None:
        """Enable webhook notifications (if URL is configured)."""
        if self.webhook_url:
            self.enabled = True
            logger.info("Webhook notifications enabled")
        else:
            logger.warning("Cannot enable webhooks: no URL configured")
