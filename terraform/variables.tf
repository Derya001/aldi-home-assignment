variable "namespace" {
    type        = string
    description = "Kubernetes namespace to deploy into"
    default     = "myapp"
}

variable "environment" {
    type        = string
    description = "Deployment environment (e.g. dev, staging, production)"
    default     = "dev"
}

variable "image_tag" {
    type        = string
    description = "Docker image tag to deploy"
    default     = "latest"
}