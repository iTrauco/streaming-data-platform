# Global TCP Load Balancer Configuration
resource "google_compute_global_address" "stream_lb" {
  name = "stream-lb-ip"
}

resource "google_compute_global_forwarding_rule" "stream_lb" {
  name                  = "stream-lb-forwarding-rule"
  ip_protocol          = "TCP"
  load_balancing_scheme = "EXTERNAL"
  port_range           = "1935"
  target               = google_compute_target_tcp_proxy.stream_proxy.id
  ip_address           = google_compute_global_address.stream_lb.id
}

resource "google_compute_target_tcp_proxy" "stream_proxy" {
  name            = "stream-tcp-proxy"
  backend_service = google_compute_backend_service.stream_backend.id
}

resource "google_compute_backend_service" "stream_backend" {
  name                  = "stream-backend"
  protocol              = "TCP"
  port_name             = "rtmp"
  load_balancing_scheme = "EXTERNAL"
  timeout_sec           = 1800
  health_checks         = [google_compute_health_check.stream_health.id]

  backend {
    group = google_compute_instance_group_manager.stream_mig.instance_group
  }
}

resource "google_compute_health_check" "stream_health" {
  name               = "stream-health-check"
  timeout_sec        = 5
  check_interval_sec = 10

  tcp_health_check {
    port = 1935
  }
}