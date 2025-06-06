"""Config flow for Tago integration."""
from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

from .const import (
    DOMAIN,
    CONF_NET_BRIDGE_URL,
    CONF_IS_TAGO_LEGACY_DEVICE
)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors = {}

        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=vol.Schema(
                    {
                        vol.Required(CONF_NET_BRIDGE_URL, default=""): str,
                        vol.Optional(CONF_IS_TAGO_LEGACY_DEVICE, default=False): bool,
                    }
                ), errors=errors
            )

        url = user_input.get(CONF_NET_BRIDGE_URL)
        is_legacy = user_input.get(CONF_IS_TAGO_LEGACY_DEVICE)
        short_name = parsed = urlparse("//" + url).hostname
        return self.async_create_entry(
            title=f'Tago Direct {short_name}',
            data={
                CONF_NET_BRIDGE_URL: url,
                CONF_IS_TAGO_LEGACY_DEVICE: is_legacy},
        )
