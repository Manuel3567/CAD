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


# Create a Cloud Storage bucket
resource "google_storage_bucket" "fileuploader_bucket" {
  name          = "fileuploader-bucket"
  force_destroy = true
  location      = "us-central1"
  storage_class = "REGIONAL"
  uniform_bucket_level_access = true
  public_access_prevention = "enforced"

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

resource "google_project_iam_binding" "service_account_firestore" {
  project = "file-uploader-403910"

  role    = "roles/datastore.owner"

  members = [
    "serviceAccount:${google_service_account.service_account.email}"
  ]
}

resource "google_cloud_run_v2_service" "cloudrun" {
  name     = "file-uploader-service"
  location = "us-central1"
  ingress = "INGRESS_TRAFFIC_ALL"

template {
  containers {
    image = "manuelhtwg/awesomefileuploader:latest"
    ports {
        container_port = 80
      }
    env {
        name  = "BUCKET_NAME"
        value = "fileuploader-bucket"
    }
  }
  service_account = google_service_account.service_account.email
  scaling {
    min_instance_count = 1
    max_instance_count = 2
  }
}
}

resource "google_cloud_run_service_iam_binding" "security" {
  location = google_cloud_run_v2_service.cloudrun.location
  service  = google_cloud_run_v2_service.cloudrun.name
  role     = "roles/run.invoker"
  members = [
    "allUsers"
  ]
}

/*
resource "google_firestore_database" "database" {
  project = "file-uploader-403910"
  name        = "(default)"
  location_id = "us-east1"
  type        = "FIRESTORE_NATIVE"
  point_in_time_recovery_enablement = "POINT_IN_TIME_RECOVERY_DISABLED"
  delete_protection_state = "DELETE_PROTECTION_ENABLED"

}
*/

output "cloud_run_dns" {
  value = google_cloud_run_v2_service.cloudrun.uri
}