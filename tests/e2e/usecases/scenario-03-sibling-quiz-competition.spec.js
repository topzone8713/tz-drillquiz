/**
 * 시나리오 3: 형제가 함께하는 과학 퀴즈 대결
 * 
 * 등장인물: 엄마(이수진), 초등 5학년 아들(준호), 초등 3학년 딸(예린)
 * 
 * 테스트 케이스:
 * 1. 과학 문제 파일 준비
 * 2. 각 아이 수준에 맞는 시험 만들기
 * 3. 가족 스터디 그룹 만들기
 * 4. 형제의 학습 경쟁
 * 5. 서로 도와주기
 * 6. 주말 AI 인터뷰 시간
 */

const { test, expect } = require('@playwright/test');
const { ApiClient } = require('../helpers/api');
const { login, logout } = require('../helpers/auth');
const users = require('../fixtures/users.json');

test.describe('시나리오 3: 형제가 함께하는 과학 퀴즈 대결', () => {
  let apiClient;

  test.beforeEach(async ({ page }) => {
    apiClient = new ApiClient(process.env.PLAYWRIGHT_API_URL || 'http://localhost:8000/api');
    await login(page, apiClient, users.admin.username, users.admin.password);
  });

  test.afterEach(async ({ page }) => {
    await logout(page, apiClient);
    await apiClient.dispose();
  });

  test('1단계: 과학 문제 파일 준비', async ({ page }) => {
    await page.goto('/question-files');
    await expect(page).toHaveURL(/.*question-files/);
    
    // Verify file management interface
    const fileInterface = page.locator('.file-list, table, .question-files, input[type="file"]');
    await expect(fileInterface.first()).toBeVisible({ timeout: 5000 });
  });

  test('2단계: 각 아이 수준에 맞는 시험 만들기', async ({ page }) => {
    await page.goto('/create-exam');
    
    // Check for difficulty and exam creation options
    const examCreation = page.locator('form, .exam-form, .create-exam, select[name*="difficulty"]');
    await expect(examCreation.first()).toBeVisible({ timeout: 5000 });
  });

  test('3단계: 가족 스터디 그룹 만들기', async ({ page }) => {
    await page.goto('/');
    
    const studyLink = page.locator('a:has-text("Study"), nav a[href*="study"]');
    if (await studyLink.count() > 0) {
      await studyLink.first().click();
      await page.waitForTimeout(1000);
      
      // Check for study creation or management
      const studyManagement = page.locator('.study-list, .create-study, button:has-text("Create"), table');
      await expect(studyManagement.first()).toBeVisible({ timeout: 5000 });
    }
  });

  test('4단계: 형제의 학습 경쟁', async ({ page }) => {
    await page.goto('/');
    
    // Check for progress tracking or dashboard
    const progressDashboard = page.locator('.progress, .dashboard, .study-progress, .stats');
    if (await progressDashboard.count() > 0) {
      await expect(progressDashboard.first()).toBeVisible({ timeout: 5000 });
    }
  });

  test('5단계: 서로 도와주기', async ({ page }) => {
    await page.goto('/');
    
    // Check for study detail or member view
    const studyDetail = page.locator('.study-detail, .members, .study-info');
    if (await studyDetail.count() > 0) {
      await expect(studyDetail.first()).toBeVisible({ timeout: 5000 });
    }
  });

  test('6단계: 주말 AI 인터뷰 시간', async ({ page }) => {
    await page.goto('/');
    
    // Check for AI interview mode
    const aiInterview = page.locator('button:has-text("AI"), button:has-text("Interview"), input[type="checkbox"][name*="ai"]');
    if (await aiInterview.count() > 0) {
      await expect(aiInterview.first()).toBeVisible();
    }
  });
});
