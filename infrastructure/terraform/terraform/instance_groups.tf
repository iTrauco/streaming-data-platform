# Instance Template for Stream Relay Servers
resource "google_compute_instance_template" "stream_template" {
  name_prefix  = "stream-relay-template-"
  machine_type = var.machine_type
  
  labels = {
    startup_version = substr(sha256(file("${path.module}/startup.sh")), 0, 32)
  }

  disk {
    source_image = "debian-cloud/debian-11"
    auto_delete  = true
    boot         = true
  }
  network_interface {
    subnetwork = google_compute_subnetwork.subnet.id
    access_config {
      // Ephemeral public IP
    }
  }
  metadata_startup_script = file("${path.module}/startup.sh")
  service_account {
    email  = google_service_account.stream_relay.email
    scopes = ["cloud-platform"]
  }
  tags = ["stream-relay"]
  lifecycle {
    create_before_destroy = true
  }
}

# Managed Instance Group
resource "google_compute_instance_group_manager" "stream_mig" {
  name = "stream-relay-mig"
  base_instance_name = "stream-relay"
  zone              = "${var.region}-b"
  version {
    instance_template = google_compute_instance_template.stream_template.id
  }
  named_port {
    name = "rtmp"
    port = 1935
  }
  auto_healing_policies {
    health_check      = google_compute_health_check.stream_health.id
    initial_delay_sec = 300
  }
  update_policy {
    type                = "PROACTIVE"
    minimal_action      = "REPLACE"
    max_surge_fixed     = 1
    max_unavailable_fixed = 0
    replacement_method  = "SUBSTITUTE"
  }
  target_size = 1  # Start with 1 instance for POC
}