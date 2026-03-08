# Cloudflared Metrics → Home Assistant Sensor Registry

## Conventions

- **Source type**
  - *direct*: expose metric as-is (with optional aggregation like sum over `conn_index`)
  - *derived*: computed from one or more metrics
  - *snapshot*: computed at scrape time from current samples
  - *since_start*: cumulative average since process start
- **state_class**
  - `measurement` for instantaneous/snapshot values
  - `total_increasing` for monotonic counters
- **Units**: `ms`, `B`, `B/s`, `s`, or unitless

## Quick navigation

- [Identity](#identity)
- [QUIC connections](#quic-connections)
- [QUIC RTT snapshot stats](#quic-rtt-snapshot-stats)
- [QUIC throughput totals](#quic-throughput-totals)
- [QUIC throughput “right now” rates](#quic-throughput-right-now-rates)
- [QUIC throughput lifetime averages](#quic-throughput-lifetime-average-rates)
- [QUIC transport “shape”](#quic-transport-shape-snapshot-sensors-bytes)
- [Since-start baseline latency](#since-start-baseline-latency-ms)
- [Go GC pause](#go-gc-pause-ms)
- [Tunnel operational metrics](#straight-tunnel-operational-metrics-direct-sensors)
- [Process health](#process-health-direct-sensors)

## Identity

| HA Sensor ID | Mapping | Description |
|---|---|---|
| `cloudflared_build_version` | **Source:** `build_info{version,goversion,revision,type}`<br>**Calc:** state = label `version`<br>**Attrs:** labels (`goversion`, `revision`, `type`)<br>**Unit:** —<br>**state_class:** — | Running cloudflared version (attrs: `goversion`, `revision`, `type`). |


## QUIC connections

| HA Sensor ID | Mapping | Description |
|---|---|---|
| `quic_active_connections` | **Source:** `quic_client_latest_rtt{conn_index}`<br>**Calc:** `count(samples)`<br>**Unit:** connections<br>**state_class:** `measurement` | Number of active QUIC connections at scrape time. |


## QUIC RTT snapshot stats

All derived from current scrape values of `quic_client_latest_rtt{conn_index}`.

| HA Sensor ID | Mapping | Description |
|---|---|---|
| `quic_latest_rtt_min_ms` | **Source:** `quic_client_latest_rtt{conn_index}`<br>**Calc:** `min(values)`<br>**Unit:** ms<br>**state_class:** `measurement` | Best (lowest) current RTT among connections. |
| `quic_latest_rtt_p50_ms` | **Source:** `quic_client_latest_rtt{conn_index}`<br>**Calc:** `p50(values)`<br>**Unit:** ms<br>**state_class:** `measurement` | Median current RTT. |
| `quic_latest_rtt_p75_ms` | **Source:** `quic_client_latest_rtt{conn_index}`<br>**Calc:** `p75(values)`<br>**Unit:** ms<br>**state_class:** `measurement` | 75th percentile current RTT. |
| `quic_latest_rtt_p95_ms` | **Source:** `quic_client_latest_rtt{conn_index}`<br>**Calc:** `p95(values)`<br>**Unit:** ms<br>**state_class:** `measurement` | 95th percentile current RTT (tail snapshot). |
| `quic_latest_rtt_avg_ms` | **Source:** `quic_client_latest_rtt{conn_index}`<br>**Calc:** `avg(values)`<br>**Unit:** ms<br>**state_class:** `measurement` | Average current RTT. |
| `quic_latest_rtt_max_ms` | **Source:** `quic_client_latest_rtt{conn_index}`<br>**Calc:** `max(values)`<br>**Unit:** ms<br>**state_class:** `measurement` | Worst (highest) current RTT among connections. |

## QUIC throughput totals

Cumulative counters since start.

| HA Sensor ID | Mapping | Description |
|---|---|---|
| `quic_sent_bytes_total` | **Source:** `quic_client_sent_bytes{conn_index}`<br>**Calc:** `sum(values over conn_index)`<br>**Unit:** B<br>**state_class:** `total_increasing` | Total bytes sent through QUIC since cloudflared start. |
| `quic_received_bytes_total` | **Source:** `quic_client_receive_bytes{conn_index}`<br>**Calc:** `sum(values over conn_index)`<br>**Unit:** B<br>**state_class:** `total_increasing` | Total bytes received through QUIC since cloudflared start. |

## QUIC throughput “right now” rates

Snapshot over last scrape interval (derived from deltas of totals above).

| HA Sensor ID | Mapping | Description |
|---|---|---|
| `quic_sent_bytes_per_second` | **Source:** `quic_sent_bytes_total`<br>**Calc:** `(total_now - total_prev) / dt_seconds`<br>**Unit:** B/s<br>**state_class:** `measurement` | Approx outbound throughput over last scrape interval. |
| `quic_received_bytes_per_second` | **Source:** `quic_received_bytes_total`<br>**Calc:** `(total_now - total_prev) / dt_seconds`<br>**Unit:** B/s<br>**state_class:** `measurement` | Approx inbound throughput over last scrape interval. |

## QUIC throughput lifetime average rates

Baseline since start.

| HA Sensor ID | Mapping | Description |
|---|---|---|
| `quic_sent_avg_bps_since_start` | **Source:** `quic_sent_bytes_total` + `process_start_time_seconds`<br>**Calc:** `total / (now_epoch - start_time)`<br>**Unit:** B/s<br>**state_class:** `measurement` | Average outbound throughput since cloudflared start. |
| `quic_recv_avg_bps_since_start` | **Source:** `quic_received_bytes_total` + `process_start_time_seconds`<br>**Calc:** `total / (now_epoch - start_time)`<br>**Unit:** B/s<br>**state_class:** `measurement` | Average inbound throughput since cloudflared start. |

## QUIC transport “shape” snapshot sensors (bytes)

Computed from current scrape values across `conn_index`.

### Congestion window

| HA Sensor ID | Mapping | Description |
|---|---|---|
| `quic_congestion_window_min_bytes` | **Source:** `quic_client_congestion_window{conn_index}`<br>**Calc:** `min(values)`<br>**Unit:** B<br>**state_class:** `measurement` | Smallest congestion window across connections. |
| `quic_congestion_window_avg_bytes` | **Source:** `quic_client_congestion_window{conn_index}`<br>**Calc:** `avg(values)`<br>**Unit:** B<br>**state_class:** `measurement` | Average congestion window across connections. |
| `quic_congestion_window_max_bytes` | **Source:** `quic_client_congestion_window{conn_index}`<br>**Calc:** `max(values)`<br>**Unit:** B<br>**state_class:** `measurement` | Largest congestion window across connections. |

### MTU

| HA Sensor ID | Mapping | Description |
|---|---|---|
| `quic_mtu_min_bytes` | **Source:** `quic_client_mtu{conn_index}`<br>**Calc:** `min(values)`<br>**Unit:** B<br>**state_class:** `measurement` | Smallest QUIC MTU across connections. |
| `quic_mtu_avg_bytes` | **Source:** `quic_client_mtu{conn_index}`<br>**Calc:** `avg(values)`<br>**Unit:** B<br>**state_class:** `measurement` | Average QUIC MTU across connections. |
| `quic_mtu_max_bytes` | **Source:** `quic_client_mtu{conn_index}`<br>**Calc:** `max(values)`<br>**Unit:** B<br>**state_class:** `measurement` | Largest QUIC MTU across connections. |

### Max UDP payload

| HA Sensor ID | Mapping | Description |
|---|---|---|
| `quic_max_udp_payload_min_bytes` | **Source:** `quic_client_max_udp_payload{conn_index}`<br>**Calc:** `min(values)`<br>**Unit:** B<br>**state_class:** `measurement` | Smallest max UDP payload across connections. |
| `quic_max_udp_payload_avg_bytes` | **Source:** `quic_client_max_udp_payload{conn_index}`<br>**Calc:** `avg(values)`<br>**Unit:** B<br>**state_class:** `measurement` | Average max UDP payload across connections. |
| `quic_max_udp_payload_max_bytes` | **Source:** `quic_client_max_udp_payload{conn_index}`<br>**Calc:** `max(values)`<br>**Unit:** B<br>**state_class:** `measurement` | Largest max UDP payload across connections. |

## Since-start baseline latency (ms)

| HA Sensor ID | Mapping | Description |
|---|---|---|
| `proxy_connect_latency_avg_since_start_ms` | **Source:** `cloudflared_proxy_connect_latency_sum` + `cloudflared_proxy_connect_latency_count`<br>**Calc:** `avg = sum/count`<br>**Attrs:** `count_since_start = count`<br>**Unit:** ms<br>**state_class:** `measurement` | Avg proxy connect latency since start (sum/count). |
| `rpc_client_latency_avg_since_start_ms` | **Source:** `cloudflared_rpc_client_latency_secs_sum{handler,method}` + `cloudflared_rpc_client_latency_secs_count{handler,method}`<br>**Calc:** `1000 * (Σsum / Σcount)`<br>**Attrs:** `calls_since_start = Σcount`<br>**Unit:** ms<br>**state_class:** `measurement` | Avg RPC client latency since start (aggregated). |
| `rpc_server_latency_avg_since_start_ms` | **Source:** `cloudflared_rpc_server_latency_secs_sum{handler,method}` + `cloudflared_rpc_server_latency_secs_count{handler,method}`<br>**Calc:** `1000 * (Σsum / Σcount)`<br>**Attrs:** `calls_since_start = Σcount`<br>**Unit:** ms<br>**state_class:** `measurement` | Avg RPC server latency since start (aggregated). |

## Go GC pause (ms)

| HA Sensor ID | Mapping | Description |
|---|---|---|
| `go_gc_pause_avg_since_start_ms` | **Source:** `go_gc_duration_seconds_sum` + `go_gc_duration_seconds_count`<br>**Calc:** `1000 * sum/count`<br>**Attrs:** `cycles_since_start = count`<br>**Unit:** ms<br>**state_class:** `measurement` | Avg stop-the-world GC pause since start. |
| `go_gc_pause_max_ms` | **Source:** `go_gc_duration_seconds{quantile="1" or "1.0"}` + `go_gc_duration_seconds_count`<br>**Calc:** `1000 * quantile(1)`<br>**Attrs:** `cycles_since_start = count`<br>**Unit:** ms<br>**state_class:** `measurement` | Worst GC pause observed (summary max quantile). |

## Straight tunnel operational metrics (direct sensors)

| HA Sensor ID | Mapping | Description |
|---|---|---|
| `cloudflared_tunnel_ha_connections` | **Source:** `cloudflared_tunnel_ha_connections`<br>**Calc:** direct<br>**Unit:** —<br>**state_class:** `measurement` | Active HA connections (cloudflared metric). |
| `cloudflared_tunnel_concurrent_requests_per_tunnel` | **Source:** `cloudflared_tunnel_concurrent_requests_per_tunnel`<br>**Calc:** direct<br>**Unit:** —<br>**state_class:** `measurement` | Concurrent proxied requests per tunnel. |
| `cloudflared_tunnel_total_requests` | **Source:** `cloudflared_tunnel_total_requests`<br>**Calc:** direct<br>**Unit:** —<br>**state_class:** `total_increasing` | Total proxied requests since start. |
| `cloudflared_tunnel_request_errors` | **Source:** `cloudflared_tunnel_request_errors`<br>**Calc:** direct<br>**Unit:** —<br>**state_class:** `total_increasing` | Total origin proxy errors since start. |
| `cloudflared_proxy_connect_streams_errors` | **Source:** `cloudflared_proxy_connect_streams_errors`<br>**Calc:** direct<br>**Unit:** —<br>**state_class:** `total_increasing` | Failures establishing/acknowledging connections. |
| `cloudflared_tcp_active_sessions` | **Source:** `cloudflared_tcp_active_sessions`<br>**Calc:** direct<br>**Unit:** —<br>**state_class:** `measurement` | Concurrent TCP sessions proxied. |
| `cloudflared_tcp_total_sessions` | **Source:** `cloudflared_tcp_total_sessions`<br>**Calc:** direct<br>**Unit:** —<br>**state_class:** `total_increasing` | Total TCP sessions proxied since start. |
| `cloudflared_udp_active_sessions` | **Source:** `cloudflared_udp_active_sessions`<br>**Calc:** direct<br>**Unit:** —<br>**state_class:** `measurement` | Concurrent UDP sessions proxied. |
| `cloudflared_udp_total_sessions` | **Source:** `cloudflared_udp_total_sessions`<br>**Calc:** direct<br>**Unit:** —<br>**state_class:** `total_increasing` | Total UDP sessions proxied since start. |
| `quic_client_total_connections` | **Source:** `quic_client_total_connections`<br>**Calc:** direct<br>**Unit:** —<br>**state_class:** `total_increasing` | QUIC connections initiated since start. |
| `quic_client_closed_connections` | **Source:** `quic_client_closed_connections`<br>**Calc:** direct<br>**Unit:** —<br>**state_class:** `total_increasing` | QUIC connections closed since start. |
| `quic_client_packet_too_big_dropped` | **Source:** `quic_client_packet_too_big_dropped`<br>**Calc:** direct<br>**Unit:** —<br>**state_class:** `total_increasing` | Packets dropped due to being too big. |

## Process health (direct sensors)

| HA Sensor ID | Mapping | Description |
|---|---|---|
| `process_start_time_seconds` | **Source:** `process_start_time_seconds`<br>**Calc:** direct; `native_value = datetime.fromtimestamp(epoch, tz=utc)`<br>**Unit:** —<br>**state_class:** —<br>**device_class:** `TIMESTAMP` | Process start time as a timezone-aware datetime. |
| `process_resident_memory_bytes` | **Source:** `process_resident_memory_bytes`<br>**Calc:** direct<br>**Unit:** B<br>**state_class:** `measurement` | Resident memory usage. |
| `process_cpu_seconds_total` | **Source:** `process_cpu_seconds_total`<br>**Calc:** direct<br>**Unit:** s<br>**state_class:** `total_increasing` | Total CPU time consumed. |
| `process_open_fds` | **Source:** `process_open_fds`<br>**Calc:** direct<br>**Unit:** —<br>**state_class:** `measurement` | Open file descriptors. |
| `process_max_fds` | **Source:** `process_max_fds`<br>**Calc:** direct<br>**Unit:** —<br>**state_class:** `measurement` | Max file descriptors allowed. |
| `process_network_receive_bytes_total` | **Source:** `process_network_receive_bytes_total`<br>**Calc:** direct<br>**Unit:** B<br>**state_class:** `total_increasing` | Total bytes received by process. |
| `process_network_transmit_bytes_total` | **Source:** `process_network_transmit_bytes_total`<br>**Calc:** direct<br>**Unit:** B<br>**state_class:** `total_increasing` | Total bytes sent by process. |