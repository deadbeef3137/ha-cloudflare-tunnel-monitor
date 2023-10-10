
# Cloudflare Tunnel Monitor Integration for Home Assistant

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
![Cloudflare Tunnel Monitor|128](https://raw.githubusercontent.com/deadbeef3137/ha-cloudflare-tunnel-monitor/master/images/cloudflare-tunnel.png)

## Description

This custom integration for Home Assistant allows users to monitor the status of their Cloudflare Tunnels directly from their Home Assistant instance. The integration fetches the status of Cloudflare Tunnels and presents it as sensor entities in Home Assistant.



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

### Via UI

1. Navigate to "Configuration" -> "Integrations" -> "+".
2. Search for "Cloudflare Tunnel Monitor" and select it.
3. Fill in the required information and click "Submit".

### Configuration Variables

- `email`: Your Cloudflare account email.
- `api_key`: Your Cloudflare Global API Key.
- `account_id`: Your Cloudflare Account ID.

## Usage

Upon successful configuration, the integration will create sensor entities for each Cloudflare Tunnel. These sensors will reflect the current status of each tunnel.

## Support

If you encounter any issues or require further assistance, please raise an issue on this [GitHub repository](https://github.com/deadbeef3137/ha-cloudflare-tunnel-monitor/issues).

## License

This integration is released under the [MIT License](https://opensource.org/licenses/MIT).

## Disclaimer

This project is not affiliated with or endorsed by Cloudflare.

