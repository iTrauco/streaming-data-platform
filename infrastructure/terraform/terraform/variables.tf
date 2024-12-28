variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "container_image" {
  description = "Container image for stream relay service"
  type        = string
  default     = "stream-relay:latest"  # This will be built later
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-east1"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
}

variable "machine_type" {
  description = "Machine type for stream relay instances"
  type        = string
  default     = "e2-standard-2"
}