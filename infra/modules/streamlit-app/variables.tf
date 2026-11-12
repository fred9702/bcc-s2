variable "name" {
  description = "Application name, used for all resource names and labels."
  type        = string
  default     = "bcc-dashboard"
}

variable "namespace" {
  description = "Namespace to create and deploy into."
  type        = string
}

variable "environment" {
  description = "Environment name exposed to the app as APP_ENV."
  type        = string
}

variable "image" {
  description = "Container image repository."
  type        = string
}

variable "image_tag" {
  description = "Container image tag; also exposed as APP_VERSION."
  type        = string
}

variable "image_pull_policy" {
  description = "IfNotPresent for locally loaded images (minikube), Always for registries."
  type        = string
  default     = "IfNotPresent"
}

variable "replicas" {
  description = "Baseline replica count (HPA min)."
  type        = number
  default     = 1
}

variable "max_replicas" {
  description = "HPA max replicas."
  type        = number
  default     = 3
}

variable "cpu_target_utilization" {
  description = "HPA target average CPU utilisation (%)."
  type        = number
  default     = 70
}

variable "resources" {
  description = "Container resource requests/limits."
  type = object({
    requests = map(string)
    limits   = map(string)
  })
  default = {
    requests = { cpu = "100m", memory = "256Mi" }
    limits   = { cpu = "500m", memory = "512Mi" }
  }
}

variable "data_files" {
  description = "Map of file name => local path, mounted via ConfigMap at /data (must total < 1 MiB)."
  type        = map(string)
}

variable "extra_env" {
  description = "Additional environment variables for the container."
  type        = map(string)
  default     = {}
}

variable "service_type" {
  description = "Kubernetes Service type."
  type        = string
  default     = "ClusterIP"
}
