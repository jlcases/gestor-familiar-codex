async function request(path, options = {}) {
  const response = await fetch(`/api${path}`, { headers: { 'Content-Type': 'application/json' }, ...options });
  if (!response.ok) throw new Error((await response.json().catch(() => null))?.detail || 'No hemos podido guardar el cambio');
  return response.status === 204 ? null : response.json();
}
export const api = {
  get: (path) => request(path),
  post: (path, body) => request(path, { method: 'POST', body: JSON.stringify(body) }),
  patch: (path) => request(path, { method: 'PATCH' }),
  delete: (path) => request(path, { method: 'DELETE' })
};
