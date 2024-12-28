# Service Account for Stream Relay instances
resource "google_service_account" "stream_relay" {
  account_id   = "stream-relay-sa"
  display_name = "Stream Relay Service Account"
}

# IAM roles for the service account
resource "google_project_iam_member" "secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.stream_relay.email}"
}

resource "google_project_iam_member" "log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.stream_relay.email}"
}

resource "google_project_iam_member" "metric_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.stream_relay.email}"
}

# Secret Manager for stream keys
resource "google_secret_manager_secret" "stream_keys" {
  secret_id = "stream-keys"
  
  replication {
    automatic = true
  }
}

# Grant access to the service account
resource "google_secret_manager_secret_iam_member" "stream_keys_access" {
  secret_id = google_secret_manager_secret.stream_keys.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.stream_relay.email}"
}