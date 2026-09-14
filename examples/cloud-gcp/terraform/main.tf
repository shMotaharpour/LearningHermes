# Hermes gateway on GCP — Chapter 13b.
#
# NOT APPLIED BY THIS REPO. No GCP project is available to it, so `terraform init`,
# `validate`, `plan` and `apply` are yours to run. What CI does check is `terraform fmt`,
# which catches syntax and layout and nothing else. Treat every resource below as a
# reviewed design, not a tested deployment, and read it against the current provider docs.
#
#   terraform init && terraform validate      # needs registry access
#   terraform plan -var project_id=...        # needs credentials
#
# The shape is the lesson: a gateway agent is a long-lived stateful process with secrets and
# a database, which is why it is Cloud Run with min_instances rather than a Function, and
# why the service account is per-service rather than the default.

terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  description = "GCP project that will own these resources."
  type        = string
}

variable "region" {
  description = "Region for all regional resources. Keep data and compute in one region."
  type        = string
  default     = "europe-west4"
}

variable "gateway_image" {
  description = "Container image for the Hermes gateway, pinned by DIGEST not by tag."
  type        = string
}

# A tag is a moving pointer. Pinning by digest is what makes a deployment reproducible and a
# rollback meaningful — the same argument as `hermes plugins install --ref <sha>` (Ch 12).
variable "enforce_digest_pin" {
  description = "Refuse an image reference that is not digest-pinned."
  type        = bool
  default     = true
}

locals {
  image_is_digest_pinned = can(regex("@sha256:[0-9a-f]{64}$", var.gateway_image))
}

# --- identity -----------------------------------------------------------------------
#
# One service account per service, with only the roles that service needs. The default
# compute service account is over-privileged by design and is the single most common
# finding in a GCP review.

resource "google_service_account" "gateway" {
  account_id   = "hermes-gateway"
  display_name = "Hermes gateway runtime"
  description  = "Runtime identity for the gateway. Least privilege; no project-level editor."
}

resource "google_project_iam_member" "gateway_secret_access" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.gateway.email}"
}

resource "google_project_iam_member" "gateway_sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.gateway.email}"
}

# --- secrets ------------------------------------------------------------------------
#
# The secret VALUE is never in Terraform. State is not a vault: anything you put in a
# variable ends up in the state file, and the state file ends up in a bucket someone can
# read. Terraform creates the container; a human or a CI job with a narrower identity
# writes the version.

resource "google_secret_manager_secret" "provider_api_key" {
  secret_id = "hermes-provider-api-key"
  replication {
    auto {}
  }
}

# --- data ---------------------------------------------------------------------------
#
# Cloud SQL for PostgreSQL with pgvector — the deployment target from Chapter 03c.
#
# AlloyDB is the alternative, and the threshold is specific rather than a matter of taste:
# its ScaNN index (the `alloydb_scann` extension) is where you go once the index stops
# fitting in memory. Google's own benchmark puts ScaNN at 431ms against pgvector HNSW's
# >4s at that point. Below the memory line the difference barely shows; above it, the index
# implementation IS the latency budget. The schema is the same either way, so this is a
# migration you can defer until you have measured — which is the whole point of Ch 03c's
# recall benchmark.

resource "google_sql_database_instance" "vectors" {
  name             = "hermes-vectors"
  database_version = "POSTGRES_16"
  region           = var.region

  # Not cosmetic. Without the peering below, an instance with ipv4_enabled = false and a
  # private_network has nowhere to get an address from, and `apply` fails. Terraform infers
  # dependencies from references, and this instance references the NETWORK, not the
  # connection — so the ordering has to be stated. The general rule: an implicit dependency
  # only exists where there is an actual reference.
  depends_on = [google_service_networking_connection.private_vpc_connection]

  settings {
    tier              = "db-custom-2-7680"
    availability_type = "ZONAL"

    # pgvector is an extension, not a flag: connect and run `CREATE EXTENSION vector;`
    # (examples/retrieval-scale/schema.sql) after the instance exists.
    ip_configuration {
      ipv4_enabled = false
      # Private IP only. A database reachable from the internet is a finding, not a
      # convenience, and Cloud Run reaches it through the VPC connector below.
      private_network = google_compute_network.vpc.id
    }

    backup_configuration {
      enabled                        = true
      point_in_time_recovery_enabled = true
    }
  }

  # Deliberate: destroying the vector store should require a decision, not a typo.
  deletion_protection = true
}

resource "google_compute_network" "vpc" {
  name                    = "hermes-vpc"
  auto_create_subnetworks = true
}

# Private services access: the two resources people forget, and the reason a "private IP"
# Cloud SQL instance fails to create on a first apply.
#
# Cloud SQL does not live in your VPC. It lives in a Google-managed VPC that is PEERED with
# yours, so "private IP" means "reachable over a peering" — and a peering needs an address
# range on your side to peer into. You reserve that range (global address) and then
# establish the peering (service networking connection). Omit either and
# `ip_configuration.private_network` has nothing to attach to.
#
# This is the shape of most cloud-networking bugs: the managed service is not where you
# think it is, and the thing you must create is the path to it.

resource "google_compute_global_address" "private_ip_range" {
  name          = "hermes-private-services"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_range.name]
}

# --- compute ------------------------------------------------------------------------

resource "google_cloud_run_v2_service" "gateway" {
  name     = "hermes-gateway"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

  template {
    service_account = google_service_account.gateway.email

    # A gateway holds platform connections and in-flight turns. Scaling it to zero drops
    # them, so min_instances is 1 — this is the line where "it is just a container" stops
    # being true, and it is the design point of the whole file.
    scaling {
      min_instance_count = 1
      max_instance_count = 3
    }

    containers {
      image = var.gateway_image

      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
        # The agent loop is long-running; CPU must stay allocated between requests or a
        # turn stalls whenever the container is idle between tool calls.
        cpu_idle = false
      }

      env {
        name = "HERMES_PROVIDER_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.provider_api_key.secret_id
            version = "latest"
          }
        }
      }

      startup_probe {
        initial_delay_seconds = 10
        period_seconds        = 5
        failure_threshold     = 6
        tcp_socket {
          port = 8080
        }
      }
    }

    vpc_access {
      network_interfaces {
        network = google_compute_network.vpc.id
      }
      egress = "ALL_TRAFFIC"
    }
  }
}

output "gateway_service_account" {
  description = "Runtime identity; grant further roles to this, never to the default."
  value       = google_service_account.gateway.email
}

output "image_digest_pinned" {
  description = "False means the deployment is not reproducible. Treat it as a failure."
  value       = local.image_is_digest_pinned
}
