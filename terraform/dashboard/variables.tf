variable "namespace" {
  description = "namespace to deploy dashboard."
  type        = string
}

variable "dashboard_name" {
  description = "kubernetes resource name and filesystem filename for the dashboard."
  type        = string
}

variable "dashboard_dir" {
  description = "filesystem directory name for the dashboard to be created in, will create dir if it does not exist."
  type        = string
}

variable "dashboard_json" {
  description = "json payload for dashboard."
  type        = string
}

variable "labels" {
  description = "Map of labels to be added to resource metadata."
  type        = map(string)
  default     = {}
}

variable "annotations" {
  description = "Map of annotations to be added to resource metadata."
  type        = map(string)
  default     = {}
}
