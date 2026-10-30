/**
 * Decoy Service: Safe runtime configuration loader.
 * No hardcoded secrets. Scanners should NOT flag this file.
 */
export async function loadRuntimeConfig() {
  try {
    const res = await fetch('/config.json');
    if (!res.ok) {
      return { apiUrl: '/api' };
    }
    return await res.json();
  } catch {
    return { apiUrl: '/api' };
  }
}

