terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "5.4.0"
    }
  }
}

provider "google" {
  credentials = file("../secrets/gcp.json")
  project     = "file-uploader-403910"
  region      = "us-central1"
  zone        = "us-central1-c"
}

variable "DATABASE_PASSWORD" {
  type = string
}
variable "IMAGE" {
  type = string
}

# Create a VPC network
resource "google_compute_network" "fileuploader_network" {
  name                    = "fileuploader"
  auto_create_subnetworks = false
}

# Create two subnets
resource "google_compute_subnetwork" "subnet1" {
  name          = "subnet1"
  region        = "us-central1"
  network       = google_compute_network.fileuploader_network.name
  ip_cidr_range = "10.0.0.0/24"
}

resource "google_compute_subnetwork" "subnet2" {
  name          = "subnet2"
  region        = "us-central1"
  network       = google_compute_network.fileuploader_network.name
  ip_cidr_range = "10.0.1.0/24"
}

# Create a PostgreSQL database
resource "google_sql_database_instance" "fileuploader_db" {
  name                = "fileuploader-db"
  database_version    = "POSTGRES_15"
  region              = "us-central1"
  deletion_protection = false
  root_password       = var.DATABASE_PASSWORD
  depends_on          = [google_service_networking_connection.peering]

  settings {
    tier = "db-f1-micro"
    ip_configuration {
      ipv4_enabled    = "true"
      private_network = google_compute_network.fileuploader_network.id
    }
  }
}

resource "google_compute_global_address" "private_ip_address" {
  name          = "private-ip-address"
  depends_on    = [google_compute_network.fileuploader_network]
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.fileuploader_network.id
}

resource "google_compute_network_peering_routes_config" "peering_routes" {
  peering              = google_service_networking_connection.peering.peering
  network              = google_compute_network.fileuploader_network.name
  import_custom_routes = true
  export_custom_routes = true
}

resource "google_sql_database" "file_uploader_db" {
  name     = "file_uploader"
  instance = google_sql_database_instance.fileuploader_db.name
}

resource "google_service_networking_connection" "peering" {
  network                 = google_compute_network.fileuploader_network.id
  depends_on              = [google_compute_network.fileuploader_network]
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_address.name]
}

# Create a Cloud Storage bucket
resource "google_storage_bucket" "fileuploader_bucket" {
  name          = "fileuploader-bucket"
  force_destroy = true
  location      = "us-central1"
  storage_class = "REGIONAL"
  uniform_bucket_level_access = true
  public_access_prevention = "enforced"

}


# Create an instance template
resource "google_compute_region_instance_template" "fileuploader_template" {
  name         = "fileuploader-template"
  depends_on   = [google_sql_database_instance.fileuploader_db]
  machine_type = "n1-standard-1"
  disk {
    source_image = var.IMAGE
  }
  service_account {
    email = google_service_account.service_account.email
    scopes = ["https://www.googleapis.com/auth/cloud-platform", "https://www.googleapis.com/auth/compute", "https://www.googleapis.com/auth/devstorage.read_write"]

  }

  network_interface {
    subnetwork = google_compute_subnetwork.subnet1.self_link
    access_config {
        network_tier = "PREMIUM"
    }
  }

  metadata_startup_script = <<EOF
#!/bin/bash
if echo "DATABASE_PASSWORD=${var.DATABASE_PASSWORD}" >> /home/manuel/.env; then
    echo "DATABASE_PASSWORD written successfully"
else
    echo "Failed to write DATABASE_PASSWORD to .env"
fi
echo "DATABASE_PASSWORD=${var.DATABASE_PASSWORD}" >> /home/manuel/.env
echo "DATABASE_HOST=${google_sql_database_instance.fileuploader_db.private_ip_address}" >> /home/manuel/.env
echo "BUCKET_NAME=${google_storage_bucket.fileuploader_bucket.name}" >> /home/manuel/.env
systemctl start awesomefileuploader.service
EOF
}

# Create an instance group
resource "google_compute_region_instance_group_manager" "fileuploader_instance_group" {
  name               = "fileuploader-group"
  base_instance_name = "fileuploader-instance"
  target_size        = 2
  depends_on         = [google_compute_region_instance_template.fileuploader_template]
  stateful_external_ip {
    interface_name = "nic0"
  }

  version {
    name              = "v1"
    instance_template = google_compute_region_instance_template.fileuploader_template.self_link

  }
  update_policy {
    type = "PROACTIVE"
    minimal_action = "REPLACE"
    instance_redistribution_type = "NONE"
    max_surge_fixed = 0
    max_unavailable_fixed = 3
    replacement_method = "RECREATE"
  }
}

# Create a health check
resource "google_compute_health_check" "fileuploader_health_check" {
  name               = "fileuploader-health-check"
  timeout_sec        = 10
  check_interval_sec = 10
  tcp_health_check {
    port = 80
  }
}

# Create a backend service
resource "google_compute_backend_service" "fileuploader_backend_service" {
  name        = "fileuploader-backend-service"
  protocol    = "HTTP"
  port_name   = "http"
  timeout_sec = 10
  backend {
    group = google_compute_region_instance_group_manager.fileuploader_instance_group.instance_group
  }
  health_checks = [google_compute_health_check.fileuploader_health_check.self_link]
}

# Create a URL map
resource "google_compute_url_map" "fileuploader_url_map" {
  name            = "fileuploader-url-map"
  default_service = google_compute_backend_service.fileuploader_backend_service.self_link
  description     = "URL Map for the FileUploader application"
}

# Create a target HTTP proxy
resource "google_compute_target_http_proxy" "fileuploader_http_proxy" {
  name    = "fileuploader-http-proxy"
  depends_on         = [google_compute_region_instance_template.fileuploader_template]
  url_map = google_compute_url_map.fileuploader_url_map.self_link
}

# Create a global forwarding rule
resource "google_compute_global_forwarding_rule" "fileuploader_forwarding_rule" {
  name                  = "fileuploader-forwarding-rule"
  load_balancing_scheme = "EXTERNAL"
  target                = google_compute_target_http_proxy.fileuploader_http_proxy.self_link
  port_range            = "80"
}

resource "google_compute_firewall" "allow-ssh-from-gcp" {
  name    = "allow-ssh-from-gcp"
  network = google_compute_network.fileuploader_network.name

  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
  direction = "INGRESS"
  source_ranges = ["35.235.240.0/20"]
}

resource "google_compute_firewall" "allow-network-traffic-in" {
  name    = "allow-network-traffic-in"
  network = google_compute_network.fileuploader_network.name

  allow {
    protocol = "tcp"
  }
  direction = "INGRESS"
  source_ranges = ["10.0.0.0/16"]
}

resource "google_compute_firewall" "allow-network-traffic-out" {
  name    = "allow-network-traffic-out"
  network = google_compute_network.fileuploader_network.name

  allow {
    protocol = "tcp"
  }
  direction = "EGRESS"
  source_ranges = ["0.0.0.0/0"]
}

resource "google_compute_firewall" "allow-http-traffic-in" {
  name    = "allow-http-traffic-in"
  network = google_compute_network.fileuploader_network.name

  allow {
    protocol = "tcp"
    ports    = ["80"]
  }
  direction = "INGRESS"
  source_ranges = ["0.0.0.0/0"]
}

resource "google_compute_firewall" "allow-healthcheck-from-gcp" {
  name    = "allow-healthcheck-from-gcp"
  network = google_compute_network.fileuploader_network.name

  allow {
    protocol = "tcp"
  }

  direction = "INGRESS"
  source_ranges = ["35.191.0.0/16", "130.211.0.0/22", "209.85.152.0/22", "209.85.204.0/22"]
}


resource "google_service_account" "service_account" {
  account_id   = "my-service-account"
  display_name = "My Service Account"
}

resource "google_project_iam_binding" "service_account_project_binding" {
  project = "file-uploader-403910"

  role    = "roles/storage.objectAdmin"

  members = [
    "serviceAccount:${google_service_account.service_account.email}"
  ]
}

# Output the IP address of the load balancer
output "load_balancer_ip" {
  value = google_compute_global_forwarding_rule.fileuploader_forwarding_rule.ip_address
}