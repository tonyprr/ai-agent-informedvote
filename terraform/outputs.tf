output "function_app_url" {
  description = "URL principal de la API de Azure Functions para las consultas"
  value       = "https://${azurerm_linux_function_app.function.default_hostname}"
}

output "function_app_hostname" {
  description = "Hostname de la Function App"
  value       = azurerm_linux_function_app.function.default_hostname
}
