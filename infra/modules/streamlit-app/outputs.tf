output "namespace" {
  value = kubernetes_namespace_v1.bccs2.metadata[0].name
}

output "service_name" {
  value = kubernetes_service_v1.bccs2.metadata[0].name
}

output "image" {
  value = "${var.image}:${var.image_tag}"
}

output "url" {
  description = "Dashboard URL via the Ingress (null when disabled)."
  value       = var.ingress_enabled ? "http://${var.ingress_host}" : null
}
