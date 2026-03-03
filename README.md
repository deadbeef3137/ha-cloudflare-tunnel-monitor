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

If a `metrics_url` is configured, the integration also scrapes cloudflared's Prometheus `/metrics` endpoint and exposes ~50 additional sensors covering QUIC RTT statistics, throughput rates, transport shape, proxy/RPC latency baselines, Go GC pause metrics, and process health counters. See [`sensor-map.md`](sensor-map.md) for the full sensor registry.

## Support

If you encounter any issues or require further assistance, please raise an issue on this [GitHub repository](https://github.com/deadbeef3137/ha-cloudflare-tunnel-monitor/issues).

## License

This integration is released under the [MIT License](https://opensource.org/licenses/MIT).

## Disclaimer

This project is not affiliated with or endorsed by Cloudflare.

