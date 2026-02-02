const { ApiClient } = require('./api');

/**
 * Login helper function
 */
async function login(page, apiClient, username, password) {
  // Try API login first
  const response = await apiClient.post('/auth/login/', {
    username,
    password,
  });

  if (response.ok) {
    const data = await response.json();
    // Set authentication token if provided
    if (data.token || data.access_token) {
      apiClient.token = data.token || data.access_token;
    }
    
    // Navigate to home page and set cookies
    await page.goto('/');
    const cookies = await page.context().cookies();
    apiClient.setCookies(cookies);
    
    return { success: true, data };
  }

  // If API login fails, try UI login
  await page.goto('/login');
  await page.fill('input[name="username"], input[type="text"]', username);
  await page.fill('input[name="password"], input[type="password"]', password);
  await page.click('button:has-text("Login"), button[type="submit"]');
  
  // Wait for navigation
  await page.waitForURL(/^\/(?!login)/, { timeout: 5000 }).catch(() => {});
  
  const cookies = await page.context().cookies();
  apiClient.setCookies(cookies);
  
  return { success: true };
}

/**
 * Logout helper function
 */
async function logout(page, apiClient) {
  // Try API logout
  try {
    await apiClient.post('/auth/logout/');
  } catch (e) {
    // Ignore API logout errors
  }

  // UI logout
  await page.goto('/');
  const logoutButton = page.locator('a:has-text("Logout"), button:has-text("Logout")');
  if (await logoutButton.count() > 0) {
    await logoutButton.click();
    await page.waitForURL(/\/login/, { timeout: 5000 }).catch(() => {});
  }

  apiClient.clearCookies();
}

/**
 * Register helper function
 */
async function register(page, apiClient, username, email, password) {
  await page.goto('/register');
  await page.fill('input[name="username"], input[type="text"]', username);
  await page.fill('input[name="email"], input[type="email"]', email);
  await page.fill('input[name="password"], input[type="password"]', password);
  await page.click('button:has-text("Register"), button[type="submit"]');
  
  // Wait for navigation
  await page.waitForURL(/^\/(?!register)/, { timeout: 5000 }).catch(() => {});
  
  const cookies = await page.context().cookies();
  apiClient.setCookies(cookies);
  
  return { success: true };
}

module.exports = { login, logout, register };
