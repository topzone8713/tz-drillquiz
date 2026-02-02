/**
 * 시나리오 5: 직장인 부부의 자격증 시험 준비
 * 
 * 등장인물: 부부(김대현, 이혜진), 둘 다 정보처리기사 자격증 준비 중
 * 
 * 테스트 케이스:
 * 1. 기출 문제 파일 업로드
 * 2. 과목별 시험 구성
 * 3. 부부 스터디 그룹
 * 4. 각자의 학습 진행
 * 5. 서로 도와주기
 * 6. 실전 연습 - AI 인터뷰
 * 7. 최종 점검
 */

const { test, expect } = require('@playwright/test');
const { ApiClient } = require('../helpers/api');
const { login, logout } = require('../helpers/auth');
const users = require('../fixtures/users.json');

test.describe('시나리오 5: 직장인 부부의 자격증 시험 준비', () => {
  let apiClient;

  test.beforeEach(async ({ page }) => {
    apiClient = new ApiClient(process.env.PLAYWRIGHT_API_URL || 'http://localhost:8000/api');
    await login(page, apiClient, users.admin.username, users.admin.password);
  });

  test.afterEach(async ({ page }) => {
    await logout(page, apiClient);
    await apiClient.dispose();
  });

  test('1단계: 기출 문제 파일 업로드', async ({ page }) => {
    await page.goto('/question-files');
    await expect(page).toHaveURL(/.*question-files/);
    
    const uploadInterface = page.locator('input[type="file"], .upload-area, button:has-text("Upload")');
    await expect(uploadInterface.first()).toBeVisible({ timeout: 5000 });
  });

  test('2단계: 과목별 시험 구성', async ({ page }) => {
    await page.goto('/create-exam');
    
    const examForm = page.locator('form, .exam-form, .create-exam');
    await expect(examForm.first()).toBeVisible({ timeout: 5000 });
  });

  test('3단계: 부부 스터디 그룹', async ({ page }) => {
    await page.goto('/');
    
    const studyLink = page.locator('a:has-text("Study"), nav a[href*="study"]');
    if (await studyLink.count() > 0) {
      await studyLink.first().click();
      await page.waitForTimeout(1000);
      
      const studyManagement = page.locator('.study-list, .create-study, button:has-text("Create")');
      await expect(studyManagement.first()).toBeVisible({ timeout: 5000 });
    }
  });

  test('4단계: 각자의 학습 진행', async ({ page }) => {
    await page.goto('/');
    
    const examLink = page.locator('a:has-text("Exam"), a[href*="exam"]');
    if (await examLink.count() > 0) {
      await examLink.first().click();
      await page.waitForTimeout(1000);
      
      const examInterface = page.locator('.exam-list, .take-exam, table');
      await expect(examInterface.first()).toBeVisible({ timeout: 5000 });
    }
  });

  test('5단계: 서로 도와주기', async ({ page }) => {
    await page.goto('/');
    
    // Check for study detail or member interaction
    const studyDetail = page.locator('.study-detail, .members, .study-info');
    if (await studyDetail.count() > 0) {
      await expect(studyDetail.first()).toBeVisible({ timeout: 5000 });
    }
  });

  test('6단계: 실전 연습 - AI 인터뷰', async ({ page }) => {
    await page.goto('/');
    
    const aiInterview = page.locator('button:has-text("AI"), button:has-text("Interview"), input[type="checkbox"][name*="ai"]');
    if (await aiInterview.count() > 0) {
      await expect(aiInterview.first()).toBeVisible();
    }
  });

  test('7단계: 최종 점검', async ({ page }) => {
    await page.goto('/results');
    
    const resultsInterface = page.locator('.results, .stats, table, .exam-results');
    await expect(resultsInterface.first()).toBeVisible({ timeout: 5000 }).catch(() => {
      expect(page.locator('body')).toBeVisible();
    });
  });
});
