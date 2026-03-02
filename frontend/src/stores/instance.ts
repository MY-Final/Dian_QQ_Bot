import { defineStore } from 'pinia'
import { ref } from 'vue'
import { instanceApi, type Instance, type InstanceCreate } from '../api'

export const useInstanceStore = defineStore('instances', () => {
  const instances = ref<Instance[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchInstances() {
    loading.value = true
    error.value = null
    try {
      const response = await instanceApi.list()
      instances.value = response.data
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to fetch instances'
    } finally {
      loading.value = false
    }
  }

  async function createInstance(data: InstanceCreate): Promise<Instance | null> {
    loading.value = true
    error.value = null
    try {
      const response = await instanceApi.create(data)
      instances.value.push(response.data)
      return response.data
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to create instance'
      return null
    } finally {
      loading.value = false
    }
  }

  async function startInstance(id: string) {
    loading.value = true
    error.value = null
    try {
      const response = await instanceApi.start(id)
      const index = instances.value.findIndex(i => i.id === id)
      if (index !== -1) {
        instances.value[index] = response.data
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to start instance'
    } finally {
      loading.value = false
    }
  }

  async function stopInstance(id: string) {
    loading.value = true
    error.value = null
    try {
      const response = await instanceApi.stop(id)
      const index = instances.value.findIndex(i => i.id === id)
      if (index !== -1) {
        instances.value[index] = response.data
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to stop instance'
    } finally {
      loading.value = false
    }
  }

  async function deleteInstance(id: string) {
    loading.value = true
    error.value = null
    try {
      await instanceApi.delete(id)
      instances.value = instances.value.filter(i => i.id !== id)
    } catch (e) {
      error.value = e instanceof Error ? e.message : 'Failed to delete instance'
    } finally {
      loading.value = false
    }
  }

  return {
    instances,
    loading,
    error,
    fetchInstances,
    createInstance,
    startInstance,
    stopInstance,
    deleteInstance,
  }
})
