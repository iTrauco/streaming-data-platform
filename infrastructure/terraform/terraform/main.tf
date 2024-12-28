terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = "us-east1"
}

# VPC and Network Configuration
resource "google_compute_network" "vpc" {
  name                    = "stream-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnet" {
  name          = "stream-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = "us-east1"
  network       = google_compute_network.vpc.id
}

# Firewall Rules
resource "google_compute_firewall" "rtmp" {
  name    = "allow-rtmp"
  network = google_compute_network.vpc.id

  allow {
    protocol = "tcp"
    ports    = ["1935"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["stream-relay"]
}