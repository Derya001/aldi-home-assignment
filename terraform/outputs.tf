output "namespace_name" {
    value = kubernetes_namespace.homework.metadata[0].name
}

output "helm_release_name" {
    value = helm_release.homework.name
}

output "helm_release_status" {
    value = helm_release.homework.status
}
