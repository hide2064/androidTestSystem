import axios from 'axios'

const client = axios.create({ baseURL: '/api/orchestrator' })

export interface Scenario {
  name: string
  display_name: string
  description: string
  version: string
  step_count: number
}

export interface TestStatus {
  status: 'idle' | 'running' | 'error'
  scenario: string | null
  device: string | null
  start_time: string | null
  elapsed: string | null
  current_step: { id: number; description: string } | null
}

export async function fetchScenarios(): Promise<Scenario[]> {
  const res = await client.get('/scenarios')
  return res.data
}

export async function fetchStatus(): Promise<TestStatus> {
  const res = await client.get('/test/status')
  return res.data
}

export async function startTest(scenarioName: string, deviceId: string) {
  const res = await client.post('/test/start', {
    scenario_name: scenarioName,
    device_id: deviceId,
  })
  return res.data
}

export async function stopTest() {
  const res = await client.post('/test/stop')
  return res.data
}

export async function fetchResults(limit = 20) {
  const res = await client.get('/results', { params: { limit } })
  return res.data
}

export async function fetchDevices() {
  const res = await client.get('/devices')
  return res.data
}
