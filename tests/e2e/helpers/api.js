/**
 * API Client for E2E tests
 */
class ApiClient {
  constructor(baseURL) {
    this.baseURL = baseURL || process.env.PLAYWRIGHT_API_URL || 'http://localhost:8000/api';
    this.cookies = [];
  }

  async request(method, endpoint, data = null, headers = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const options = {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...headers,
      },
    };

    if (this.cookies.length > 0) {
      options.headers['Cookie'] = this.cookies.map(c => `${c.name}=${c.value}`).join('; ');
    }

    if (data) {
      options.body = JSON.stringify(data);
    }

    const response = await fetch(url, options);
    
    // Extract cookies from response
    const setCookieHeader = response.headers.get('set-cookie');
    if (setCookieHeader) {
      // Parse cookies (simplified)
      const cookies = setCookieHeader.split(',').map(c => {
        const parts = c.split(';')[0].split('=');
        return { name: parts[0].trim(), value: parts[1]?.trim() || '' };
      });
      this.cookies.push(...cookies);
    }

    return response;
  }

  async get(endpoint, headers = {}) {
    return this.request('GET', endpoint, null, headers);
  }

  async post(endpoint, data, headers = {}) {
    return this.request('POST', endpoint, data, headers);
  }

  async put(endpoint, data, headers = {}) {
    return this.request('PUT', endpoint, data, headers);
  }

  async delete(endpoint, headers = {}) {
    return this.request('DELETE', endpoint, null, headers);
  }

  setCookies(cookies) {
    this.cookies = cookies;
  }

  clearCookies() {
    this.cookies = [];
  }

  dispose() {
    this.clearCookies();
  }
}

module.exports = { ApiClient };
