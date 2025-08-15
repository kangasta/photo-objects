output "cluster" {
  value = data.upcloud_kubernetes_cluster.this
}

output "objsto" {
  value = {
    access_key = upcloud_managed_object_storage_user_access_key.django.access_key_id
    secret_key = upcloud_managed_object_storage_user_access_key.django.secret_access_key
    host       = tolist(upcloud_managed_object_storage.this.endpoint)[0].domain_name
  }
}
