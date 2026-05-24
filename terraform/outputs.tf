output "function_app_url" {
  description = "URL principal de la API de Azure Functions para las consultas"
  value       = "https://${azurerm_function_app_flex_consumption.function.default_hostname}"
}

output "function_app_hostname" {
  description = "Hostname de la Function App"
  value       = azurerm_function_app_flex_consumption.function.default_hostname
}
