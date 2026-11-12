locals {
  labels = {
    "app.kubernetes.io/name"       = var.name
    "app.kubernetes.io/instance"   = "${var.name}-${var.environment}"
    "app.kubernetes.io/version"    = var.image_tag
    "app.kubernetes.io/managed-by" = "terraform"
    "environment"                  = var.environment
  }
  selector  = { "app.kubernetes.io/name" = var.name }
  data      = { for k, path in var.data_files : k => file(path) }
  data_hash = sha256(jsonencode(local.data))
  port      = 8501
  env = merge({
    APP_ENV                              = var.environment
    APP_VERSION                          = var.image_tag
    DATA_DIR                             = "/data"
    HOME                                 = "/tmp"
    STREAMLIT_BROWSER_GATHER_USAGE_STATS = "false"
  }, var.extra_env)
}

resource "kubernetes_namespace_v1" "bccs2" {
  metadata {
    name = var.namespace
    labels = {
      environment                          = var.environment
      "pod-security.kubernetes.io/enforce" = "restricted"
    }
  }
}

resource "kubernetes_config_map_v1" "data" {
  metadata {
    name      = "${var.name}-data"
    namespace = kubernetes_namespace_v1.bccs2.metadata[0].name
    labels    = local.labels
  }
  data = local.data
}

resource "kubernetes_deployment_v1" "bccs2" {
  metadata {
    name      = var.name
    namespace = kubernetes_namespace_v1.bccs2.metadata[0].name
    labels    = local.labels
  }

  spec {
    replicas = var.replicas
    selector { match_labels = local.selector }

    strategy {
      type = "RollingUpdate"
      rolling_update {
        max_unavailable = "0"
        max_surge       = "1"
      }
    }

    template {
      metadata {
        labels = local.labels
        annotations = {
          # roll pods when the CSV data changes
          "checksum/data" = local.data_hash
        }
      }

      spec {
        automount_service_account_token = false

        security_context {
          run_as_non_root = true
          run_as_user     = 10001
          run_as_group    = 10001
          fs_group        = 10001
          seccomp_profile { type = "RuntimeDefault" }
        }

        container {
          name              = "app"
          image             = "${var.image}:${var.image_tag}"
          image_pull_policy = var.image_pull_policy

          port {
            name           = "http"
            container_port = local.port
          }

          dynamic "env" {
            for_each = local.env
            content {
              name  = env.key
              value = env.value
            }
          }

          resources {
            requests = var.resources.requests
            limits   = var.resources.limits
          }

          startup_probe {
            http_get {
              path = "/_stcore/health"
              port = "http"
            }
            period_seconds    = 5
            failure_threshold = 24
          }

          readiness_probe {
            http_get {
              path = "/_stcore/health"
              port = "http"
            }
            period_seconds = 10
          }

          liveness_probe {
            http_get {
              path = "/_stcore/health"
              port = "http"
            }
            period_seconds    = 20
            failure_threshold = 3
          }

          security_context {
            # set explicitly: the provider otherwise sends runAsNonRoot=false, which PSA "restricted" rejects
            run_as_non_root            = true
            allow_privilege_escalation = false
            read_only_root_filesystem  = true
            capabilities { drop = ["ALL"] }
          }

          volume_mount {
            name       = "data"
            mount_path = "/data"
            read_only  = true
          }

          volume_mount {
            name       = "tmp"
            mount_path = "/tmp"
          }
        }

        volume {
          name = "data"
          config_map { name = kubernetes_config_map_v1.data.metadata[0].name }
        }

        volume {
          name = "tmp"
          empty_dir { size_limit = "64Mi" }
        }
      }
    }
  }

  wait_for_rollout = true

  lifecycle {
    # HPA owns the live replica count
    ignore_changes = [spec[0].replicas]
  }
}

resource "kubernetes_service_v1" "bccs2" {
  metadata {
    name      = var.name
    namespace = kubernetes_namespace_v1.bccs2.metadata[0].name
    labels    = local.labels
  }
  spec {
    type     = var.service_type
    selector = local.selector
    port {
      name        = "http"
      port        = 80
      target_port = "http"
    }
  }
}

resource "kubernetes_horizontal_pod_autoscaler_v2" "bccs2" {
  metadata {
    name      = var.name
    namespace = kubernetes_namespace_v1.bccs2.metadata[0].name
    labels    = local.labels
  }
  spec {
    min_replicas = var.replicas
    max_replicas = var.max_replicas
    scale_target_ref {
      api_version = "apps/v1"
      kind        = "Deployment"
      name        = kubernetes_deployment_v1.bccs2.metadata[0].name
    }
    metric {
      type = "Resource"
      resource {
        name = "cpu"
        target {
          type                = "Utilization"
          average_utilization = var.cpu_target_utilization
        }
      }
    }
  }
}

resource "kubernetes_pod_disruption_budget_v1" "bccs2" {
  count = var.replicas > 1 ? 1 : 0
  metadata {
    name      = var.name
    namespace = kubernetes_namespace_v1.bccs2.metadata[0].name
    labels    = local.labels
  }
  spec {
    min_available = "1"
    selector { match_labels = local.selector }
  }
}

resource "kubernetes_network_policy_v1" "bccs2" {
  metadata {
    name      = "${var.name}-ingress"
    namespace = kubernetes_namespace_v1.bccs2.metadata[0].name
  }
  spec {
    pod_selector { match_labels = local.selector }
    policy_types = ["Ingress"]
    ingress {
      ports {
        port     = "http"
        protocol = "TCP"
      }
    }
  }
}

resource "kubernetes_ingress_v1" "bccs2" {
  count = var.ingress_enabled ? 1 : 0

  metadata {
    name      = var.name
    namespace = kubernetes_namespace_v1.bccs2.metadata[0].name
    labels    = local.labels
    annotations = merge({
      # Streamlit keeps a long-lived websocket per session; nginx's 60s default drops it
      "nginx.ingress.kubernetes.io/proxy-read-timeout" = "3600"
      "nginx.ingress.kubernetes.io/proxy-send-timeout" = "3600"
      # TODO(prod): TLS via cert-manager, e.g. cert-manager.io/cluster-issuer = "letsencrypt"
    }, var.ingress_annotations)
  }

  spec {
    ingress_class_name = var.ingress_class_name

    rule {
      host = var.ingress_host
      http {
        path {
          path      = "/"
          path_type = "Prefix"
          backend {
            service {
              name = kubernetes_service_v1.bccs2.metadata[0].name
              port { name = "http" }
            }
          }
        }
      }
    }
  }

  wait_for_load_balancer = false
}
