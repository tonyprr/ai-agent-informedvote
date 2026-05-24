terraform {
  required_version = ">= 1.0.0"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0" # FC1 Flex Consumption requires provider >= 4.x
    }
  }
}

provider "azurerm" {
  features {}
  subscription_id = var.subscription_id
}

# 1. Resource Group
resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
}

# 2. Storage Account (Required by Azure Functions Flex Consumption)
resource "azurerm_storage_account" "storage" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.rg.name
  location                 = azurerm_resource_group.rg.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

# 3. App Service Plan (Flex Consumption - FC1)
# FC1 es el nuevo plan serverless avanzado de Azure:
# - Escala más rápido que Y1 (Consumption clásico)
# - Soporta instancias concurrentes configurables
# - Capa gratuita: 250,000 ejecuciones y 100,000 vCPU-s/mes
resource "azurerm_service_plan" "plan" {
  name                = "asp-rag-backend-flex"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  os_type             = "Linux"
  sku_name            = "FC1" # FC1 = Flex Consumption
}

# 4. Storage Container (requerido por azurerm_function_app_flex_consumption)
resource "azurerm_storage_container" "func_container" {
  name                  = "azure-webjobs-hosts"
  storage_account_id    = azurerm_storage_account.storage.id
  container_access_type = "private"
}

# 3. Application Insights
resource "azurerm_application_insights" "ai_app" {
  name                = "ai-${var.function_name}"
  location            = azurerm_resource_group.rg.location
  resource_group_name = azurerm_resource_group.rg.name
  application_type    = "web"
}

# 5. Flex Consumption Function App (recurso dedicado para FC1 en AzureRM 4.x)
resource "azurerm_function_app_flex_consumption" "function" {
  name                = var.function_name
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  service_plan_id     = azurerm_service_plan.plan.id

  # Apunta al contenedor de Storage con autenticación por Managed Identity
  storage_container_type      = "blobContainer"
  storage_container_endpoint  = "${azurerm_storage_account.storage.primary_blob_endpoint}${azurerm_storage_container.func_container.name}"
  storage_authentication_type = "SystemAssignedIdentity"

  # Runtime: declarado como atributos directos (no en site_config)
  runtime_name    = "python"
  runtime_version = "3.13"

  # Configuración de instancias concurrentes para carga RAG
  instance_memory_in_mb  = 2048
  maximum_instance_count = 10

  # Habilitar identidad gestionada (System-Assigned) para acceso a Storage
  identity {
    type = "SystemAssigned"
  }

  site_config {}

  app_settings = {
    "APPLICATIONINSIGHTS_CONNECTION_STRING" = azurerm_application_insights.ai_app.connection_string
    "GOOGLE_API_KEY"      = var.google_api_key
    "PINECONE_API_KEY"    = var.pinecone_api_key
    "PINECONE_INDEX_NAME" = var.pinecone_index_name
    "AzureWebJobsStorage__accountName"      = azurerm_storage_account.storage.name
    # FUNCTIONS_WORKER_RUNTIME es gestionado automáticamente por runtime_name
  }
}

# 6. Role Assignment: Managed Identity → Storage Blob Data Owner
# Requerido para que la función acceda al contenedor de Storage de forma segura
resource "azurerm_role_assignment" "function_storage_role" {
  scope                = azurerm_storage_account.storage.id
  role_definition_name = "Storage Blob Data Owner"
  principal_id         = azurerm_function_app_flex_consumption.function.identity[0].principal_id
}
