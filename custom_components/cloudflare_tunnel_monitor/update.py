"""Update entities showing whether a tunnel's cloudflared connectors are current."""

from __future__ import annotations

from typing import Any

from homeassistant.components.update import UpdateEntity, UpdateEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import issue_registry as ir
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .changelog import RELEASE_NOTES_PAGE_URL, build_release_notes
from .changelog import parse_version as _parse_version
from .const import (
    CONF_ACCOUNT_ID,
    CONF_REPAIR_ISSUES,
    DEFAULT_REPAIR_ISSUES,
    DOMAIN,
)
from .sensor import _build_connectors

PARALLEL_UPDATES = 0


class CloudflaredTunnelUpdate(CoordinatorEntity, UpdateEntity):
    """Report the cloudflared version of a tunnel's connectors.

    cloudflared runs outside Home Assistant, so the entity can't install
    anything: it only shows the version, release notes and allows skipping.
    The installed version is the oldest version among the tunnel's connectors;
    with no connectors online it is unknown.

    Optionally an outdated tunnel also raises a repair issue: Home Assistant
    only lists update entities that can be installed on the Settings page.
    """

    _attr_supported_features = UpdateEntityFeature.RELEASE_NOTES
    _attr_title = "cloudflared"

    def __init__(
        self,
        coordinator: Any,
        details_coordinator: Any,
        tunnel_id: str,
        tunnel_name: str,
        entry_id: str,
        account_id: str,
        repair_issues: bool = False,
    ) -> None:
        """Initialize the update entity."""
        super().__init__(coordinator)
        self._details = details_coordinator
        self._tunnel_id = tunnel_id
        self._tunnel_name = tunnel_name
        self._repair_issues = repair_issues
        self._issue_id: str | None = None
        self._attr_name = f"Cloudflare Tunnel {tunnel_name} cloudflared"
        self._attr_unique_id = f"{DOMAIN}_{tunnel_id}_cloudflared_update"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, f"{entry_id}_cloudflare_tunnels_{account_id}")},
            "name": "Cloudflare Tunnels",
            "manufacturer": "Cloudflare",
        }

    async def async_added_to_hass(self) -> None:
        """Also refresh state when the details coordinator updates."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self._details.async_add_listener(self._handle_coordinator_update)
        )
        self._sync_issue()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Write state and keep the repair issue in sync."""
        super()._handle_coordinator_update()
        self._sync_issue()

    async def async_skip(self) -> None:
        """Skip the latest version and drop its repair issue."""
        await super().async_skip()
        self._sync_issue()

    async def async_clear_skipped(self) -> None:
        """Clear the skipped version and restore the repair issue."""
        await super().async_clear_skipped()
        self._sync_issue()

    @callback
    def _sync_issue(self) -> None:
        """Create or delete the repair issue for an outdated tunnel.

        The issue id includes the latest version, so ignoring the issue in
        Repairs applies to that release only. While the version is unknown
        (no connector online) the issue is left as it is.
        """
        state = self.state
        if state not in (STATE_ON, STATE_OFF):
            return
        latest = self.latest_version
        wanted = (
            f"outdated_cloudflared_{self._tunnel_id}_{latest}"
            if self._repair_issues and state == STATE_ON
            else None
        )
        if self._issue_id and self._issue_id != wanted:
            ir.async_delete_issue(self.hass, DOMAIN, self._issue_id)
        if wanted:
            release = self._latest_release() or {}
            tag = release.get("tag") or latest
            ir.async_create_issue(
                self.hass,
                DOMAIN,
                wanted,
                is_fixable=False,
                is_persistent=False,
                severity=ir.IssueSeverity.WARNING,
                learn_more_url=RELEASE_NOTES_PAGE_URL.format(tag=tag),
                translation_key="outdated_cloudflared",
                translation_placeholders={
                    "tunnel": self._tunnel_name,
                    "installed": self.installed_version or "?",
                    "latest": latest or "?",
                },
            )
        self._issue_id = wanted

    def _latest_release(self) -> dict[str, Any] | None:
        return (self._details.data or {}).get("latest_release")

    @property
    def installed_version(self) -> str | None:
        """Return the oldest cloudflared version among the tunnel's connectors."""
        tunnel = next(
            (t for t in self.coordinator.data or [] if t.get("id") == self._tunnel_id),
            None,
        )
        if not tunnel:
            return None
        # Use the live connections (refreshed every minute); connector details
        # are only refreshed every 10 minutes and may describe connectors that
        # have since been replaced (e.g. after a cloudflared restart).
        clients = (self._details.data or {}).get("clients", {}).get(self._tunnel_id)
        versions = [
            c["version"] for c in _build_connectors(tunnel, clients, None) if c["version"]
        ]
        if not versions:
            return None
        parsed = [(v, _parse_version(v)) for v in set(versions)]
        comparable = [item for item in parsed if item[1] is not None]
        if not comparable:
            return sorted(versions)[0]
        return min(comparable, key=lambda item: item[1])[0]

    @property
    def latest_version(self) -> str | None:
        """Return the latest cloudflared release."""
        release = self._latest_release()
        return release.get("version") if release else None

    @property
    def release_url(self) -> str | None:
        """Return the URL of the latest release."""
        release = self._latest_release()
        return release.get("url") if release else None

    async def async_release_notes(self) -> str | None:
        """Return the changes between the installed and the latest version."""
        release = self._latest_release()
        if not release:
            return None
        return build_release_notes(
            self.installed_version,
            release.get("version"),
            release.get("notes"),
            release.get("changes"),
            release.get("tag"),
        )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up one cloudflared update entity per tunnel."""
    data = hass.data[DOMAIN][entry.entry_id]
    api_coordinator = data["api_coordinator"]
    details_coordinator = data["details_coordinator"]
    account_id = entry.data[CONF_ACCOUNT_ID]
    repair_issues = entry.options.get(CONF_REPAIR_ISSUES, DEFAULT_REPAIR_ISSUES)
    known_tunnel_ids: set[str] = set()

    if not repair_issues:
        # Option turned off: remove issues raised earlier.
        for issue_id, issue in list(ir.async_get(hass).issues.items()):
            if issue_id[0] == DOMAIN and issue_id[1].startswith("outdated_cloudflared_"):
                ir.async_delete_issue(hass, DOMAIN, issue.issue_id)

    @callback
    def _add_new_tunnels() -> None:
        new_entities = []
        for tunnel in api_coordinator.data or []:
            tunnel_id = tunnel.get("id")
            tunnel_name = tunnel.get("name")
            if not tunnel_id or not tunnel_name or tunnel_id in known_tunnel_ids:
                continue
            known_tunnel_ids.add(tunnel_id)
            new_entities.append(
                CloudflaredTunnelUpdate(
                    api_coordinator,
                    details_coordinator,
                    tunnel_id,
                    tunnel_name,
                    entry.entry_id,
                    account_id,
                    repair_issues,
                )
            )
        if new_entities:
            async_add_entities(new_entities)

    _add_new_tunnels()
    entry.async_on_unload(api_coordinator.async_add_listener(_add_new_tunnels))
