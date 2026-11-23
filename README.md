# Cloudflare Tunnel Monitor Home Assistant Integration

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
![Cloudflare Tunnel Monitor|128](https://raw.githubusercontent.com/deadbeef3137/ha-cloudflare-tunnel-monitor/master/images/logo.png)

## Description

This custom integration for Home Assistant allows users to monitor the status of their Cloudflare Tunnels directly from their Home Assistant instance. The integration fetches the status of Cloudflare Tunnels and presents it as sensor entities in Home Assistant.

Prometheus metrics support has been implemented - thanks to @tannerln7.

## Installation

### Via HACS (Home Assistant Community Store)

1. Navigate to the HACS page on your Home Assistant instance.
2. Go to the "Integrations" tab and click the "Explore & Add Repositories" button.
3. Search for "Cloudflare Tunnel Monitor" and select it.
4. Click on "Install this repository in HACS".
5. Restart your Home Assistant instance.

### Manual Installation

1. Clone this repository or download the zip file.
2. Copy the `cloudflare_tunnel_monitor` directory from the `custom_components` directory in this repository to the `custom_components` directory on your Home Assistant instance.
3. Restart your Home Assistant instance.

## Configuration

### Cloudflare Setup
<span><strong style="color:deepskyblue;">1. Copy your Account ID.</strong></span>

![Account ID](https://raw.githubusercontent.com/deadbeef3137/imagenes-readme/master/AccountID.png)

<span><strong style="color:deepskyblue;">2. Create an API Token.</strong></span>

![API Token](https://raw.githubusercontent.com/deadbeef3137/imagenes-readme/master/API-Token.png)


### Via UI

1. Navigate to "Configuration" -> "Integrations" -> "+".
2. Search for "Cloudflare Tunnel Monitor" and select it.
3. Fill in the required information and click "Submit".

### Configuration Variables

- `api_key`: Your Cloudflare API Token with `Account:Cloudflare Tunnel:Read` permissions
- `account_id`: Your Cloudflare Account ID.
- `metrics_url` *(optional)*: The URL of your local cloudflared Prometheus metrics endpoint (e.g. `http://10.0.30.5:20241/metrics`). When provided, the integration creates additional sensors for QUIC transport, throughput, latency, process health, and more.


## Usage

Upon successful configuration, the integration will create sensor entities for each Cloudflare Tunnel reflecting current tunnel status (healthy / degraded / inactive / down).

### Tunnel attributes

Each tunnel sensor also carries attributes with details about the tunnel, its connectors (the running `cloudflared` instances) and its routes. The status is refreshed every minute; connector details and routes every 10 minutes; the latest `cloudflared` release is checked on GitHub every 6 hours.

| Attribute | Description |
|---|---|
| `tunnel_id`, `tunnel_type`, `created_at` | Tunnel identity |
| `config_source`, `remote_config` | Whether the tunnel is managed from the Cloudflare dashboard (`cloudflare`) or a local config file (`local`) |
| `conns_active_at`, `conns_inactive_at` | When the tunnel last became connected / disconnected |
| `connector_count`, `connection_count` | Number of connectors and of their connections to the Cloudflare edge |
| `cloudflared_versions` | Versions run by the connectors |
| `latest_cloudflared_version` | Latest `cloudflared` release on GitHub |
| `update_available` | `true` if any connector runs an older version (`null` if unknown or no connectors) |
| `origin_ips` | Public IPs the connectors connect from |
| `edge_locations` | Cloudflare data centers the connectors are connected to |
| `connectors` | Per connector: `client_id`, `version`, `is_latest`, `origin_ips`, `edge_locations`, `connections`, `pending_reconnect`, `opened_at`, `arch`, `run_at` |
| `hostnames`, `ingress` | Public hostname routes (hostname, optional path, service). Only for dashboard-managed tunnels |
| `private_networks` | Private network routes (CIDR, comment, virtual network), when configured |

The `connectors`, `ingress`, `private_networks` and `edge_locations` attributes are excluded from the recorder. If the API token lacks permission for some of these details, only those attributes are missing and a single warning is logged.

Example template:

```yaml
{{ state_attr('sensor.cloudflare_tunnels_cloudflare_tunnel_mytunnel', 'update_available') }}
```

### cloudflared update entities

Each tunnel also gets an update entity (e.g. `update.cloudflare_tunnels_cloudflare_tunnel_mytunnel_cloudflared`) that shows the oldest `cloudflared` version among its connectors and the latest release, so outdated connectors appear under **Settings → Updates**. cloudflared runs outside Home Assistant, so there is no install button; *Skip* is available. The release notes list the changes of every version between the installed and the latest one, taken from cloudflared's `RELEASE_NOTES` and `CHANGES.md` (the GitHub release pages only contain checksums). With no connector online the entity is `unknown`.

Home Assistant lists update entities without an install option only under **Settings → System → Updates**, not on the Settings page itself. To get a more visible notice, enable **repair issues** in the integration options (**Configure** on the integration page; off by default): when a tunnel runs an outdated cloudflared, the integration then creates a repair issue (Settings → Repairs) linking to the release notes. It disappears once the connector is updated or the version is skipped on the update entity; ignoring it in Repairs hides it for that release only.

Alternatively, use your own automation, for example:

```yaml
alias: cloudflared update available
triggers:
  - trigger: state
    entity_id:
      - update.cloudflare_tunnels_cloudflare_tunnel_mytunnel_cloudflared
    to: "on"
actions:
  - action: persistent_notification.create
    data:
      notification_id: "cloudflared_update_{{ trigger.entity_id }}"
      title: cloudflared update available
      message: >-
        {{ state_attr(trigger.entity_id, 'friendly_name') }}:
        {{ state_attr(trigger.entity_id, 'installed_version') }} →
        {{ state_attr(trigger.entity_id, 'latest_version') }}
```

If a `metrics_url` is configured, the integration also scrapes cloudflared's Prometheus `/metrics` endpoint and exposes ~50 additional sensors covering QUIC RTT statistics, throughput rates, transport shape, proxy/RPC latency baselines, Go GC pause metrics, and process health counters. See [`sensor-map.md`](sensor-map.md) for the full sensor registry.

## Support

If you encounter any issues or require further assistance, please raise an issue on this [GitHub repository](https://github.com/deadbeef3137/ha-cloudflare-tunnel-monitor/issues).

## License

This integration is released under the [MIT License](https://opensource.org/licenses/MIT).

## Disclaimer

This project is not affiliated with or endorsed by Cloudflare.

