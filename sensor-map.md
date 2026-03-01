# Cloudflared Metrics → Home Assistant Sensor Registry

## Conventions
- **Source type**:
  - *direct*: expose metric as-is (with optional aggregation like sum over conn_index)
  - *derived*: computed from one or more metrics
  - *snapshot*: computed at scrape time from current samples
  - *since_start*: cumulative average since process start
- **state_class**:
  - `measurement` for instantaneous/snapshot values
  - `total_increasing` for monotonic counters
- **Units**:
  - `ms`, `B`, `B/s`, `s`, or unitless

---

## Identity

| HA Sensor ID | Source metric(s) | Calc / Aggregation | Unit | state_class | Description |
|---|---|---|---|---|---|
| cloudflared_build_version | build_info{version,goversion,revision,type} | state = label `version`; attrs = labels | — | — | Running cloudflared version (attrs: goversion, revision, type). |

---

## QUIC connections

| HA Sensor ID | Source metric(s) | Calc / Aggregation | Unit | state_class | Description |
|---|---|---|---|---|---|
| quic_active_connections | quic_client_latest_rtt{conn_index} | count(samples) | connections | measurement | Number of active QUIC connections at scrape time. |

---

## QUIC RTT snapshot stats (computed from per-conn latest RTT)

All derived from current scrape values of `quic_client_latest_rtt{conn_index}`.

| HA Sensor ID | Source metric(s) | Calc / Aggregation | Unit | state_class | Description |
|---|---|---|---|---|---|
| quic_latest_rtt_min_ms | quic_client_latest_rtt{conn_index} | min(values) | ms | measurement | Best (lowest) current RTT among connections. |
| quic_latest_rtt_p50_ms | quic_client_latest_rtt{conn_index} | p50(values) | ms | measurement | Median current RTT. |
| quic_latest_rtt_p75_ms | quic_client_latest_rtt{conn_index} | p75(values) | ms | measurement | 75th percentile current RTT. |
| quic_latest_rtt_p95_ms | quic_client_latest_rtt{conn_index} | p95(values) | ms | measurement | 95th percentile current RTT (tail snapshot). |
| quic_latest_rtt_avg_ms | quic_client_latest_rtt{conn_index} | avg(values) | ms | measurement | Average current RTT. |
| quic_latest_rtt_max_ms | quic_client_latest_rtt{conn_index} | max(values) | ms | measurement | Worst (highest) current RTT among connections. |

---

## QUIC throughput totals (cumulative counters since start)

| HA Sensor ID | Source metric(s) | Calc / Aggregation | Unit | state_class | Description |
|---|---|---|---|---|---|
| quic_sent_bytes_total | quic_client_sent_bytes{conn_index} | sum(values over conn_index) | B | total_increasing | Total bytes sent through QUIC since cloudflared start. |
| quic_received_bytes_total | quic_client_receive_bytes{conn_index} | sum(values over conn_index) | B | total_increasing | Total bytes received through QUIC since cloudflared start. |

---

## QUIC throughput “right now” rates (snapshot over last scrape interval)

These are derived from deltas of the totals above.

| HA Sensor ID | Source metric(s) | Calc / Aggregation | Unit | state_class | Description |
|---|---|---|---|---|---|
| quic_sent_bytes_per_second | quic_sent_bytes_total | (total_now - total_prev) / dt_seconds | B/s | measurement | Approx outbound throughput over last scrape interval. |
| quic_received_bytes_per_second | quic_received_bytes_total | (total_now - total_prev) / dt_seconds | B/s | measurement | Approx inbound throughput over last scrape interval. |

**Edge cases:** first scrape → None; counter reset (delta < 0) → None or clamp to 0 (choose one consistently).

---

## QUIC throughput lifetime average rates (baseline since start)

| HA Sensor ID | Source metric(s) | Calc / Aggregation | Unit | state_class | Description |
|---|---|---|---|---|---|
| quic_sent_avg_bps_since_start | quic_sent_bytes_total + process_start_time_seconds | total / (now_epoch - start_time) | B/s | measurement | Average outbound throughput since cloudflared start. |
| quic_recv_avg_bps_since_start | quic_received_bytes_total + process_start_time_seconds | total / (now_epoch - start_time) | B/s | measurement | Average inbound throughput since cloudflared start. |

---

## QUIC transport “shape” snapshot sensors (bytes)

Computed from current scrape values across conn_index.

| HA Sensor ID | Source metric(s) | Calc / Aggregation | Unit | state_class | Description |
|---|---|---|---|---|---|
| quic_congestion_window_min_bytes | quic_client_congestion_window{conn_index} | min(values) | B | measurement | Smallest congestion window across connections. |
| quic_congestion_window_avg_bytes | quic_client_congestion_window{conn_index} | avg(values) | B | measurement | Average congestion window across connections. |
| quic_congestion_window_max_bytes | quic_client_congestion_window{conn_index} | max(values) | B | measurement | Largest congestion window across connections. |
| quic_mtu_min_bytes | quic_client_mtu{conn_index} | min(values) | B | measurement | Smallest QUIC MTU across connections. |
| quic_mtu_avg_bytes | quic_client_mtu{conn_index} | avg(values) | B | measurement | Average QUIC MTU across connections. |
| quic_mtu_max_bytes | quic_client_mtu{conn_index} | max(values) | B | measurement | Largest QUIC MTU across connections. |
| quic_max_udp_payload_min_bytes | quic_client_max_udp_payload{conn_index} | min(values) | B | measurement | Smallest max UDP payload across connections. |
| quic_max_udp_payload_avg_bytes | quic_client_max_udp_payload{conn_index} | avg(values) | B | measurement | Average max UDP payload across connections. |
| quic_max_udp_payload_max_bytes | quic_client_max_udp_payload{conn_index} | max(values) | B | measurement | Largest max UDP payload across connections. |

---

## Since-start baseline latency (ms)

| HA Sensor ID | Source metric(s) | Calc / Aggregation | Unit | state_class | Description |
|---|---|---|---|---|---|
| proxy_connect_latency_avg_since_start_ms | cloudflared_proxy_connect_latency_sum + cloudflared_proxy_connect_latency_count | avg = sum/count; attr `count_since_start` = count | ms | measurement | Avg proxy connect latency since start (sum/count). |
| rpc_client_latency_avg_since_start_ms | cloudflared_rpc_client_latency_secs_sum{handler,method} + cloudflared_rpc_client_latency_secs_count{handler,method} | 1000 * (Σsum / Σcount); attr `calls_since_start` = Σcount | ms | measurement | Avg RPC client latency since start (aggregated). |
| rpc_server_latency_avg_since_start_ms | cloudflared_rpc_server_latency_secs_sum{handler,method} + cloudflared_rpc_server_latency_secs_count{handler,method} | 1000 * (Σsum / Σcount); attr `calls_since_start` = Σcount | ms | measurement | Avg RPC server latency since start (aggregated). |

---

## Go GC pause (ms)

| HA Sensor ID | Source metric(s) | Calc / Aggregation | Unit | state_class | Description |
|---|---|---|---|---|---|
| go_gc_pause_avg_since_start_ms | go_gc_duration_seconds_sum + go_gc_duration_seconds_count | 1000 * sum/count; attr `cycles_since_start` = count | ms | measurement | Avg stop-the-world GC pause since start. |
| go_gc_pause_max_ms | go_gc_duration_seconds{quantile="1" or "1.0"} + go_gc_duration_seconds_count | 1000 * quantile(1); attr `cycles_since_start` = count | ms | measurement | Worst GC pause observed (summary max quantile). |

---

## Straight tunnel operational metrics (direct sensors)

| HA Sensor ID | Source metric(s) | Calc / Aggregation | Unit | state_class | Description |
|---|---|---|---|---|---|
| cloudflared_tunnel_ha_connections | cloudflared_tunnel_ha_connections | direct | — | measurement | Active HA connections (cloudflared metric). |
| cloudflared_tunnel_concurrent_requests_per_tunnel | cloudflared_tunnel_concurrent_requests_per_tunnel | direct | — | measurement | Concurrent proxied requests per tunnel. |
| cloudflared_tunnel_total_requests | cloudflared_tunnel_total_requests | direct | — | total_increasing | Total proxied requests since start. |
| cloudflared_tunnel_request_errors | cloudflared_tunnel_request_errors | direct | — | total_increasing | Total origin proxy errors since start. |
| cloudflared_proxy_connect_streams_errors | cloudflared_proxy_connect_streams_errors | direct | — | total_increasing | Failures establishing/acknowledging connections. |
| cloudflared_tcp_active_sessions | cloudflared_tcp_active_sessions | direct | — | measurement | Concurrent TCP sessions proxied. |
| cloudflared_tcp_total_sessions | cloudflared_tcp_total_sessions | direct | — | total_increasing | Total TCP sessions proxied since start. |
| cloudflared_udp_active_sessions | cloudflared_udp_active_sessions | direct | — | measurement | Concurrent UDP sessions proxied. |
| cloudflared_udp_total_sessions | cloudflared_udp_total_sessions | direct | — | total_increasing | Total UDP sessions proxied since start. |
| quic_client_total_connections | quic_client_total_connections | direct | — | total_increasing | QUIC connections initiated since start. |
| quic_client_closed_connections | quic_client_closed_connections | direct | — | total_increasing | QUIC connections closed since start. |
| quic_client_packet_too_big_dropped | quic_client_packet_too_big_dropped | direct | — | total_increasing | Packets dropped due to being too big. |

---

## Process health (direct sensors)

| HA Sensor ID | Source metric(s) | Calc / Aggregation | Unit | state_class | Description |
|---|---|---|---|---|---|
| process_start_time_seconds | process_start_time_seconds | direct; `native_value` returns `datetime.fromtimestamp(epoch, tz=utc)` | — | — | Process start time as a timezone-aware datetime (`device_class=TIMESTAMP`). |
| process_resident_memory_bytes | process_resident_memory_bytes | direct | B | measurement | Resident memory usage. |
| process_cpu_seconds_total | process_cpu_seconds_total | direct | s | total_increasing | Total CPU time consumed. |
| process_open_fds | process_open_fds | direct | — | measurement | Open file descriptors. |
| process_max_fds | process_max_fds | direct | — | measurement | Max file descriptors allowed. |
| process_network_receive_bytes_total | process_network_receive_bytes_total | direct | B | total_increasing | Total bytes received by process. |
| process_network_transmit_bytes_total | process_network_transmit_bytes_total | direct | B | total_increasing | Total bytes sent by process. |