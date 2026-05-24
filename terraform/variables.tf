variable "subscription_id" {
  type        = string
  description = "ID de la suscripción de Azure. Ejecuta 'az account show --query id -o tsv' para obtenerlo."
}

variable "resource_group_name" {
  type    = string
  default = "rg-voto-informado"
}

variable "location" {
  type    = string
  default = "East US 2"
}

variable "storage_account_name" {
  type    = string
  default = "stavotoinformado"
}

variable "function_name" {
  type    = string
  default = "func-rag-backend"
}

variable "google_api_key" {
  type      = string
  sensitive = true
}

variable "pinecone_api_key" {
  type      = string
  sensitive = true
}

variable "pinecone_index_name" {
  type    = string
  default = "multipdf-rag"
}
