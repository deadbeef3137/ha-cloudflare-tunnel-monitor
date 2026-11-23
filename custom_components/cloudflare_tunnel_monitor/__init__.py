import asyncio
import logging
import re
import time
from datetime import timedelta
from typing import Any

import aiohttp
import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .changelog import (
    CHANGES_URL,
    RELEASE_NOTES_URL,
    parse_changes,
    parse_release_notes,
)
from .const import (
    CONF_ACCOUNT_ID,
    CONF_API_KEY,
    CONF_METRICS_URL,
    DETAILS_UPDATE_INTERVAL,
    DOMAIN,
    LATEST_VERSION_UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)

_SAMPLE_RE = re.compile(
    r"^([a-zA-Z_:][a-zA-Z0-9_:]*)"
    r"(?:\{([^}]*)\})?"
    r"\s+"
    r"([-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?)"
    r"(?:\s+\d+)?$"
)


def parse_prometheus_text(text: str) -> dict[str, dict[str, Any]]:
    """Parse Prometheus exposition text into unlabeled and labeled metric groups."""
    parsed: dict[str, dict[str, Any]] = {"unlabeled": {}, "labeled": {}}

    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        try:
            match = _SAMPLE_RE.match(line)
            if not match:
                continue

            metric_name, labels_str, value_str = match.groups()
            value = float(value_str)

            if labels_str:
                labels = dict(re.findall(r'(\w+)="([^"]*)"', labels_str))
                parsed["labeled"].setdefault(metric_name, []).append(
                    {"labels": labels, "value": value}
                )
            else:
                parsed["unlabeled"][metric_name] = value
        except Exception:
            continue

    return parsed


class CloudflareApiCoordinator(DataUpdateCoordinator[list[dict[str, Any]]]):
    """Coordinator for Cloudflare tunnel API data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the Cloudflare API coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_api_{entry.entry_id}",
            update_interval=timedelta(minutes=1),
        )
        self.api_key = entry.data[CONF_API_KEY]
        self.account_id = entry.data[CONF_ACCOUNT_ID]
        self.entry_id = entry.entry_id

    async def _async_update_data(self) -> list[dict[str, Any]]:
        """Fetch current tunnel list from the Cloudflare API."""
        session = async_get_clientsession(self.hass)
        url = (
            f"https://api.cloudflare.com/client/v4/accounts/"
            f"{self.account_id}/cfd_tunnel?is_deleted=false"
        )
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            async with async_timeout.timeout(10):
                response = await session.get(url, headers=headers)
                response.raise_for_status()
                data = await response.json()

            return data.get("result", [])
        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(f"Error fetching Cloudflare API data: {err}") from err


PLATFORMS = ["sensor", "update"]

CLOUDFLARE_API_BASE = "https://api.cloudflare.com/client/v4"
CLOUDFLARED_LATEST_RELEASE_URL = (
    "https://api.github.com/repos/cloudflare/cloudflared/releases/latest"
)


class CloudflareDetailsCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for slower-changing tunnel details.

    Collects connector details, ingress rules (public hostnames) of remotely
    managed tunnels, private network routes and the latest cloudflared release.
    Every source is optional: a failing request keeps the previous value so a
    token without a given permission only loses that piece of information.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api_coordinator: CloudflareApiCoordinator,
    ) -> None:
        """Initialize the details coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_details_{entry.entry_id}",
            update_interval=DETAILS_UPDATE_INTERVAL,
        )
        self.api_key = entry.data[CONF_API_KEY]
        self.account_id = entry.data[CONF_ACCOUNT_ID]
        self.api_coordinator = api_coordinator
        self._latest_checked: float | None = None
        self._failed_sources: set[str] = set()
        self.data = {
            "clients": {},
            "configurations": {},
            "routes": {},
            "latest_version": None,
            "latest_release": None,
        }

    async def _api_get(self, path: str) -> Any:
        """GET a Cloudflare API path and return its result payload."""
        session = async_get_clientsession(self.hass)
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        async with async_timeout.timeout(10):
            response = await session.get(
                f"{CLOUDFLARE_API_BASE}/accounts/{self.account_id}/{path}",
                headers=headers,
            )
            response.raise_for_status()
            data = await response.json()
        return data.get("result")

    def _source_failed(self, source: str, err: Exception) -> None:
        """Log a failed source once (warning), then at debug level."""
        if source in self._failed_sources:
            _LOGGER.debug("Fetching %s failed again: %s", source, err)
            return
        self._failed_sources.add(source)
        _LOGGER.warning(
            "Fetching %s failed, the related attributes will be missing: %s",
            source,
            err,
        )

    def _source_ok(self, source: str) -> None:
        """Mark a source as working again."""
        if source in self._failed_sources:
            self._failed_sources.discard(source)
            _LOGGER.info("Fetching %s works again", source)

    async def _fetch(self, source: str, path: str) -> tuple[bool, Any]:
        """Fetch one API path, returning (ok, result)."""
        try:
            result = await self._api_get(path)
        except (aiohttp.ClientError, TimeoutError, ValueError) as err:
            self._source_failed(source, err)
            return False, None
        self._source_ok(source)
        return True, result

    async def _fetch_text(self, url: str) -> str | None:
        """Fetch a text file, returning None on failure (changelogs are optional)."""
        session = async_get_clientsession(self.hass)
        try:
            async with async_timeout.timeout(10):
                response = await session.get(url)
                response.raise_for_status()
                return await response.text()
        except (aiohttp.ClientError, TimeoutError) as err:
            _LOGGER.debug("Fetching %s failed: %s", url, err)
            return None

    async def _fetch_latest_release(self) -> dict[str, Any] | None:
        """Fetch the latest cloudflared release and its changelog from GitHub.

        The GitHub release body only lists checksums, so the change notes come
        from the RELEASE_NOTES and CHANGES.md files at the release tag.
        """
        session = async_get_clientsession(self.hass)
        async with async_timeout.timeout(10):
            response = await session.get(
                CLOUDFLARED_LATEST_RELEASE_URL,
                headers={"Accept": "application/vnd.github+json"},
            )
            response.raise_for_status()
            data = await response.json()
        tag = data.get("tag_name")
        if not isinstance(tag, str):
            return None
        notes_text, changes_text = await asyncio.gather(
            self._fetch_text(RELEASE_NOTES_URL.format(tag=tag)),
            self._fetch_text(CHANGES_URL.format(tag=tag)),
        )
        return {
            "version": tag.lstrip("v"),
            "tag": tag,
            "url": data.get("html_url"),
            "notes": parse_release_notes(notes_text) if notes_text else {},
            "changes": parse_changes(changes_text) if changes_text else {},
        }

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch connector details, ingress rules, routes and latest version."""
        previous = self.data
        tunnels = self.api_coordinator.data or []
        tunnel_ids = [t["id"] for t in tunnels if t.get("id")]
        remote_ids = [t["id"] for t in tunnels if t.get("id") and t.get("remote_config")]

        client_results = await asyncio.gather(
            *(
                self._fetch("tunnel connectors", f"cfd_tunnel/{tid}/connections")
                for tid in tunnel_ids
            )
        )
        config_results = await asyncio.gather(
            *(
                self._fetch("tunnel configuration", f"cfd_tunnel/{tid}/configurations")
                for tid in remote_ids
            )
        )

        clients: dict[str, list[dict[str, Any]]] = {}
        for tid, (ok, result) in zip(tunnel_ids, client_results, strict=True):
            if ok:
                clients[tid] = result or []
            elif tid in previous["clients"]:
                clients[tid] = previous["clients"][tid]

        configurations: dict[str, dict[str, Any]] = {}
        for tid, (ok, result) in zip(remote_ids, config_results, strict=True):
            if ok:
                configurations[tid] = result or {}
            elif tid in previous["configurations"]:
                configurations[tid] = previous["configurations"][tid]

        ok, result = await self._fetch(
            "private network routes", "teamnet/routes?is_deleted=false&per_page=1000"
        )
        if ok:
            routes: dict[str, list[dict[str, Any]]] = {}
            for route in result or []:
                if route.get("tunnel_id"):
                    routes.setdefault(route["tunnel_id"], []).append(route)
        else:
            routes = previous["routes"]

        latest_release = previous["latest_release"]
        now = time.monotonic()
        if (
            self._latest_checked is None
            or now - self._latest_checked
            >= LATEST_VERSION_UPDATE_INTERVAL.total_seconds()
        ):
            try:
                latest_release = await self._fetch_latest_release() or latest_release
                self._latest_checked = now
                self._source_ok("latest cloudflared release")
            except (aiohttp.ClientError, TimeoutError, ValueError) as err:
                self._source_failed("latest cloudflared release", err)

        return {
            "clients": clients,
            "configurations": configurations,
            "routes": routes,
            "latest_version": latest_release["version"] if latest_release else None,
            "latest_release": latest_release,
        }


class CloudflaredMetricsCoordinator(DataUpdateCoordinator[dict[str, dict[str, Any]]]):
    """Coordinator for scraping and parsing cloudflared Prometheus metrics.

    Security note: The cloudflared /metrics endpoint may expose internal
    operational data. Users should bind it to localhost or firewall access,
    and provide a URL reachable only by Home Assistant.
    """

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, metrics_url: str
    ) -> None:
        """Initialize the cloudflared metrics coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_metrics_{entry.entry_id}",
            update_interval=timedelta(minutes=1),
        )
        self.metrics_url = metrics_url
        self._prev_sent_total: float | None = None
        self._prev_recv_total: float | None = None
        self._prev_mono: float | None = None
        self.sent_rate: float | None = None
        self.recv_rate: float | None = None

    async def _async_update_data(self) -> dict[str, dict[str, Any]]:
        """Fetch metrics text, parse samples, and compute throughput rates."""
        session = async_get_clientsession(self.hass)

        try:
            async with async_timeout.timeout(10):
                response = await session.get(self.metrics_url)
                response.raise_for_status()
                text = await response.text()
        except (aiohttp.ClientError, TimeoutError) as err:
            _LOGGER.warning("Error fetching cloudflared metrics: %s", err)
            raise UpdateFailed(f"Error fetching cloudflared metrics: {err}") from err

        parsed = parse_prometheus_text(text)

        sent_total = sum(
            sample["value"]
            for sample in parsed["labeled"].get("quic_client_sent_bytes", [])
        )
        recv_total = sum(
            sample["value"]
            for sample in parsed["labeled"].get("quic_client_receive_bytes", [])
        )

        now_mono = time.monotonic()
        sent_rate: float | None = None
        recv_rate: float | None = None

        if self._prev_mono is not None:
            dt = now_mono - self._prev_mono
            if 0 < dt < 600:
                if self._prev_sent_total is not None:
                    sent_delta = sent_total - self._prev_sent_total
                    if sent_delta >= 0:
                        sent_rate = sent_delta / dt
                if self._prev_recv_total is not None:
                    recv_delta = recv_total - self._prev_recv_total
                    if recv_delta >= 0:
                        recv_rate = recv_delta / dt

        self.sent_rate = sent_rate
        self.recv_rate = recv_rate
        self._prev_sent_total = sent_total
        self._prev_recv_total = recv_total
        self._prev_mono = now_mono

        return parsed


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Cloudflare Tunnel component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Cloudflare Tunnel from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    api_coordinator = CloudflareApiCoordinator(hass, entry)
    await api_coordinator.async_config_entry_first_refresh()

    # Details are optional: never fail setup because of them.
    details_coordinator = CloudflareDetailsCoordinator(hass, entry, api_coordinator)
    await details_coordinator.async_refresh()

    metrics_coordinator: CloudflaredMetricsCoordinator | None = None
    metrics_url = entry.data.get(CONF_METRICS_URL)
    if metrics_url:
        metrics_coordinator = CloudflaredMetricsCoordinator(hass, entry, metrics_url)
        try:
            await metrics_coordinator.async_refresh()
        except Exception as err:
            _LOGGER.warning(
                "Initial metrics refresh failed; continuing without metrics coordinator: %s",
                err,
            )
            metrics_coordinator = None

    hass.data[DOMAIN][entry.entry_id] = {
        "api_coordinator": api_coordinator,
        "details_coordinator": details_coordinator,
        "metrics_coordinator": metrics_coordinator,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))

    return True


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    else:
        _LOGGER.error("Failed to unload entry: %s", entry.entry_id)

    return unload_ok
