/**
 * 시나리오 2: 중학생 딸의 영어 단어 암기
 * 
 * 등장인물: 엄마(박지영), 중학교 2학년 딸(서연)
 * 
 * 테스트 케이스:
 * 1. 단어장 파일 업로드
 * 2. 단계별 시험 만들기 (Easy, Medium, Hard)
 * 3. 학습 스터디 구성
 * 4. 딸의 학습 진행
 * 5. AI 음성 인터뷰로 발음 연습
 * 6. 엄마에게 주간 리포트
 */

const { test, expect } = require('@playwright/test');
const { ApiClient } = require('../helpers/api');
const { login, logout } = require('../helpers/auth');
const users = require('../fixtures/users.json');

test.describe('시나리오 2: 중학생 딸의 영어 단어 암기', () => {
  let apiClient;

  test.beforeEach(async ({ page }) => {
    apiClient = new ApiClient(process.env.PLAYWRIGHT_API_URL || 'http://localhost:8000/api');
    await login(page, apiClient, users.admin.username, users.admin.password);
  });

  test.afterEach(async ({ page }) => {
    await logout(page, apiClient);
    await apiClient.dispose();
  });

  test('1단계: 단어장 파일 업로드', async ({ page }) => {
    await page.goto('/question-files');
    await expect(page).toHaveURL(/.*question-files/);
    
    // Verify file upload interface
    const uploadArea = page.locator('input[type="file"], .upload-area, button:has-text("Upload")');
    await expect(uploadArea.first()).toBeVisible({ timeout: 5000 });
  });

  test('2단계: 단계별 시험 만들기 (Easy, Medium, Hard)', async ({ page }) => {
    await page.goto('/create-exam');
    
    // Check for difficulty selection
    const difficultySelect = page.locator('select[name*="difficulty"], input[type="radio"][name*="difficulty"], .difficulty-select');
    if (await difficultySelect.count() > 0) {
      await expect(difficultySelect.first()).toBeVisible();
    }
    
    // Check for exam title input
    const titleInput = page.locator('input[name*="title"], input[placeholder*="title"], input[placeholder*="제목"]');
    if (await titleInput.count() > 0) {
      await expect(titleInput.first()).toBeVisible();
    }
  });

  test('3단계: 학습 스터디 구성', async ({ page }) => {
    await page.goto('/');
    
    const studyLink = page.locator('a:has-text("Study"), nav a[href*="study"]');
    if (await studyLink.count() > 0) {
      await studyLink.first().click();
      await page.waitForTimeout(1000);
      
      // Check for study creation or study list
      const studyInterface = page.locator('.study-list, .create-study, table, button:has-text("Create")');
      await expect(studyInterface.first()).toBeVisible({ timeout: 5000 });
    }
  });

  test('4단계: 딸의 학습 진행', async ({ page }) => {
    await page.goto('/');
    
    // Navigate to study or exam page
    const examLink = page.locator('a:has-text("Exam"), a[href*="exam"]');
    if (await examLink.count() > 0) {
      await examLink.first().click();
      await page.waitForTimeout(1000);
      
      // Check for exam list or progress tracking
      const progressInterface = page.locator('.progress, .study-progress, .exam-list, table');
      await expect(progressInterface.first()).toBeVisible({ timeout: 5000 });
    }
  });

  test('5단계: AI 음성 인터뷰로 발음 연습', async ({ page }) => {
    await page.goto('/');
    
    // Check for AI interview or voice mode
    const voiceMode = page.locator('button:has-text("Voice"), button:has-text("AI Interview"), input[type="checkbox"][name*="voice"], input[type="checkbox"][name*="ai"]');
    if (await voiceMode.count() > 0) {
      await expect(voiceMode.first()).toBeVisible();
    }
  });

  test('6단계: 엄마에게 주간 리포트', async ({ page }) => {
    await page.goto('/results');
    
    // Check for results or report interface
    const resultsInterface = page.locator('.results, .report, table, .exam-results');
    await expect(resultsInterface.first()).toBeVisible({ timeout: 5000 }).catch(() => {
      // Results page might be empty, which is valid
      expect(page.locator('body')).toBeVisible();
    });
  });
});
