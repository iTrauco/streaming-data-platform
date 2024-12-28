output "lb_ip_address" {
  description = "Global Load Balancer IP Address for RTMP input"
  value       = google_compute_global_address.stream_lb.address
}

output "instance_template_name" {
  description = "Name of the instance template"
  value       = google_compute_instance_template.stream_template.name
}

output "service_account_email" {
  description = "Email of the service account used by stream relay instances"
  value       = google_service_account.stream_relay.email
}

output "secret_name" {
  description = "Name of the Secret Manager secret storing stream keys"
  value       = google_secret_manager_secret.stream_keys.name
}

output "healthcheck_self_link" {
  description = "Self link of the health check"
  value       = google_compute_health_check.stream_health.self_link
}

output "obs_rtmp_url" {
  description = "RTMP URL to use in OBS"
  value       = "rtmp://${google_compute_global_address.stream_lb.address}/live"
}