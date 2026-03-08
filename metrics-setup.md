  
  

## Enable Cloudflared Tunnel Metrics
### Official Cloudflare documentation: 
1. Open this link and follow the OS-specific steps for editing your Cloudflared Tunnel run command.  
2. Once you reach the step where you can modify the tunnel run command, use the information below to add the appropriate `--metrics` parameter for your setup.  

>https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/configure-tunnels/cloudflared-parameters/#update-tunnel-run-parameters 
## Add the Metrics Flag
In the existing run command, add `--metrics <address>:<port>` after `tunnel` and before `run`

### Format:
```sh
cloudflared tunnel --metrics <ip-address>:<port> run --token YOUR_TUNNEL_TOKEN
```
### LocalHost only: 
```sh
cloudflared tunnel --metrics 127.0.0.1:20241 run --token YOUR_TUNNEL_TOKEN
```
- Use this if your Home Assistant server and your Cloudflared Tunnel are installed on the **`same machine`**.  
- This will expose the tunnel metrics only to the machine's **`localhost IP`** on the port you choose. The **`default port`** is **`20241`**.
    - You can choose any port you like. However, you **`must`** ensure you specify the **`same port number`** when setting up the integration in Home Assistant.

### LAN IP:
```sh
cloudflared tunnel --metrics 192.168.1.123:20241 --token YOUR_TUNNEL_TOKEN
```
- Use this if your Home Assistant server and your Cloudflared Tunnel are installed on **`separate machines`**.  
- This will expose the tunnel metrics over the Cloudflare Tunnel machine's **`LAN IP`** on the port you choose. The **`default port`** is **`20241`**.  
    - You can choose any port you like. However, you **`must`** ensure you specify the **`same port number`** when setting up the integration in Home Assistant.**

## Restart Cloudflared

After updating the run command, follow the remaining steps from the Cloudflare docs for saving and restarting the Cloudflare Tunnel. 
