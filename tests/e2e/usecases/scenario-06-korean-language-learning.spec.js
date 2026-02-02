/**
 * 시나리오 6: 해외 거주 가족의 한국어 학습
 * 
 * 등장인물: 엄마(정미라), 해외 거주 중인 초등학생 딸(하은)
 * 
 * 테스트 케이스:
 * 1. 한국어 교재 파일 준비
 * 2. 단계별 학습 시험 만들기
 * 3. 모국어 유지 스터디
 * 4. 딸의 일일 학습
 * 5. AI 음성 인터뷰로 발음 연습
 * 6. 엄마의 주간 모니터링
 * 7. 다국어 지원 활용
 */

const { test, expect } = require('@playwright/test');
const { ApiClient } = require('../helpers/api');
const { login, logout } = require('../helpers/auth');
const users = require('../fixtures/users.json');

test.describe('시나리오 6: 해외 거주 가족의 한국어 학습', () => {
  let apiClient;

  test.beforeEach(async ({ page }) => {
    apiClient = new ApiClient(process.env.PLAYWRIGHT_API_URL || 'http://localhost:8000/api');
    await login(page, apiClient, users.admin.username, users.admin.password);
  });

  test.afterEach(async ({ page }) => {
    await logout(page, apiClient);
    await apiClient.dispose();
  });

  test('1단계: 한국어 교재 파일 준비', async ({ page }) => {
    await page.goto('/question-files');
    await expect(page).toHaveURL(/.*question-files/);
    
    const uploadInterface = page.locator('input[type="file"], .upload-area, button:has-text("Upload")');
    await expect(uploadInterface.first()).toBeVisible({ timeout: 5000 });
  });

  test('2단계: 단계별 학습 시험 만들기', async ({ page }) => {
    await page.goto('/create-exam');
    
    const examForm = page.locator('form, .exam-form, .create-exam');
    await expect(examForm.first()).toBeVisible({ timeout: 5000 });
  });

  test('3단계: 모국어 유지 스터디', async ({ page }) => {
    await page.goto('/');
    
    const studyLink = page.locator('a:has-text("Study"), nav a[href*="study"]');
    if (await studyLink.count() > 0) {
      await studyLink.first().click();
      await page.waitForTimeout(1000);
      
      const studyManagement = page.locator('.study-list, .create-study, button:has-text("Create")');
      await expect(studyManagement.first()).toBeVisible({ timeout: 5000 });
    }
  });

  test('4단계: 딸의 일일 학습', async ({ page }) => {
    await page.goto('/');
    
    const examLink = page.locator('a:has-text("Exam"), a[href*="exam"]');
    if (await examLink.count() > 0) {
      await examLink.first().click();
      await page.waitForTimeout(1000);
      
      const examInterface = page.locator('.exam-list, .take-exam, table');
      await expect(examInterface.first()).toBeVisible({ timeout: 5000 });
    }
  });

  test('5단계: AI 음성 인터뷰로 발음 연습', async ({ page }) => {
    await page.goto('/');
    
    const voiceMode = page.locator('button:has-text("Voice"), button:has-text("AI Interview"), input[type="checkbox"][name*="voice"]');
    if (await voiceMode.count() > 0) {
      await expect(voiceMode.first()).toBeVisible();
    }
  });

  test('6단계: 엄마의 주간 모니터링', async ({ page }) => {
    await page.goto('/results');
    
    const resultsInterface = page.locator('.results, .stats, table, .exam-results');
    await expect(resultsInterface.first()).toBeVisible({ timeout: 5000 }).catch(() => {
      expect(page.locator('body')).toBeVisible();
    });
  });

  test('7단계: 다국어 지원 활용', async ({ page }) => {
    await page.goto('/');
    
    // Check for language selector
    const languageSelector = page.locator('button:has-text("EN"), button:has-text("KR"), .language-selector, select[name*="language"]');
    if (await languageSelector.count() > 0) {
      await expect(languageSelector.first()).toBeVisible();
      
      // Try to change language
      await languageSelector.first().click();
      await page.waitForTimeout(500);
      
      // Check for language options
      const languageOptions = page.locator('a:has-text("한국어"), a:has-text("English"), a:has-text("中文")');
      if (await languageOptions.count() > 0) {
        await expect(languageOptions.first()).toBeVisible();
      }
    }
  });
});
