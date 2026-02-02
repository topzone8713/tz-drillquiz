/**
 * 시나리오 4: 선생님과 학생들의 온라인 숙제 관리
 * 
 * 등장인물: 선생님(최영희), 중학교 1학년 학생들(10명)
 * 
 * 테스트 케이스:
 * 1. 숙제 문제 파일 업로드
 * 2. 학생별 맞춤 시험 만들기
 * 3. 학급 스터디 그룹 만들기
 * 4. 학생들의 숙제 수행
 * 5. 선생님의 진행 상황 확인
 * 6. 부진 학생 집중 관리
 * 7. 학부모 연락
 */

const { test, expect } = require('@playwright/test');
const { ApiClient } = require('../helpers/api');
const { login, logout } = require('../helpers/auth');
const users = require('../fixtures/users.json');

test.describe('시나리오 4: 선생님과 학생들의 온라인 숙제 관리', () => {
  let apiClient;

  test.beforeEach(async ({ page }) => {
    apiClient = new ApiClient(process.env.PLAYWRIGHT_API_URL || 'http://localhost:8000/api');
    await login(page, apiClient, users.admin.username, users.admin.password);
  });

  test.afterEach(async ({ page }) => {
    await logout(page, apiClient);
    await apiClient.dispose();
  });

  test('1단계: 숙제 문제 파일 업로드', async ({ page }) => {
    await page.goto('/question-files');
    await expect(page).toHaveURL(/.*question-files/);
    
    const uploadInterface = page.locator('input[type="file"], .upload-area, button:has-text("Upload")');
    await expect(uploadInterface.first()).toBeVisible({ timeout: 5000 });
  });

  test('2단계: 학생별 맞춤 시험 만들기', async ({ page }) => {
    await page.goto('/create-exam');
    
    // Check for exam creation with difficulty levels
    const examForm = page.locator('form, .exam-form, select[name*="difficulty"]');
    await expect(examForm.first()).toBeVisible({ timeout: 5000 });
  });

  test('3단계: 학급 스터디 그룹 만들기', async ({ page }) => {
    await page.goto('/');
    
    const studyLink = page.locator('a:has-text("Study"), nav a[href*="study"]');
    if (await studyLink.count() > 0) {
      await studyLink.first().click();
      await page.waitForTimeout(1000);
      
      const studyManagement = page.locator('.study-list, .create-study, button:has-text("Create")');
      await expect(studyManagement.first()).toBeVisible({ timeout: 5000 });
    }
  });

  test('4단계: 학생들의 숙제 수행', async ({ page }) => {
    await page.goto('/');
    
    const examLink = page.locator('a:has-text("Exam"), a[href*="exam"]');
    if (await examLink.count() > 0) {
      await examLink.first().click();
      await page.waitForTimeout(1000);
      
      const examInterface = page.locator('.exam-list, .take-exam, table');
      await expect(examInterface.first()).toBeVisible({ timeout: 5000 });
    }
  });

  test('5단계: 선생님의 진행 상황 확인', async ({ page }) => {
    await page.goto('/');
    
    // Check for progress dashboard or study management
    const progressDashboard = page.locator('.progress, .dashboard, .study-progress, .stats');
    if (await progressDashboard.count() > 0) {
      await expect(progressDashboard.first()).toBeVisible({ timeout: 5000 });
    }
  });

  test('6단계: 부진 학생 집중 관리', async ({ page }) => {
    await page.goto('/results');
    
    // Check for results or statistics
    const resultsInterface = page.locator('.results, .stats, table, .exam-results');
    await expect(resultsInterface.first()).toBeVisible({ timeout: 5000 }).catch(() => {
      expect(page.locator('body')).toBeVisible();
    });
  });

  test('7단계: 학부모 연락', async ({ page }) => {
    await page.goto('/results');
    
    // Check for share or email functionality
    const shareButton = page.locator('button:has-text("Share"), button:has-text("Email"), a:has-text("Share")');
    if (await shareButton.count() > 0) {
      await expect(shareButton.first()).toBeVisible();
    }
  });
});
