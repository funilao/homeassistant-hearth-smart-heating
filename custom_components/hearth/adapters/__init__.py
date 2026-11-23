"""Device adapter layer."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.helpers import device_registry as dr, entity_registry as er

from .generic_climate import GenericClimateAdapter

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .base import DeviceAdapter

_LOGGER = logging.getLogger(__name__)


def create_adapter(
    hass: HomeAssistant, entity_id: str
) -> DeviceAdapter:
    """Create the appropriate adapter for a climate entity."""
    zigbee_backend = _detect_zigbee_backend(hass, entity_id)
    if zigbee_backend is not None:
        from .danfoss_ally import DanfossAllyAdapter

        _LOGGER.info("Detected Danfoss Ally device: %s (backend: %s)", entity_id, zigbee_backend)
        return DanfossAllyAdapter(hass, entity_id, zigbee_backend)
    return GenericClimateAdapter(hass, entity_id)


def _detect_zigbee_backend(hass: HomeAssistant, entity_id: str) -> str | None:
    """Detect which Zigbee backend a Danfoss Ally device is on.

    Returns "zha", "z2m", or None (not a Danfoss device / not on Zigbee).
    """
    entity_reg = er.async_get(hass)
    entity_entry = entity_reg.async_get(entity_id)
    if not entity_entry or not entity_entry.device_id:
        return None

    device_reg = dr.async_get(hass)
    device = device_reg.async_get(entity_entry.device_id)
    if not device:
        return None

    # Check manufacturer/model
    manufacturer = (device.manufacturer or "").lower()
    model = (device.model or "").lower()

    is_danfoss = "danfoss" in manufacturer or "ally" in model
    is_popp = "d5x84yu" in manufacturer and "et093wrg" in model
    if not (is_danfoss or is_popp):
        return None

    # Determine which Zigbee backend (if any)
    backend_domains = {domain for domain, _ in device.identifiers}
    if "zha" in backend_domains:
        return "zha"
    if "mqtt" in backend_domains:
        return "z2m"

    return None
