/**
 * 문제 파싱 관련 공통 유틸리티 함수들
 */

/**
 * 난이도를 정규화합니다.
 * @param {string} difficulty - 원본 난이도
 * @returns {string} 정규화된 난이도
 */
export function normalizeDifficulty(difficulty) {
  const diff = difficulty.toLowerCase()
  if (diff.includes('easy')) return 'Easy'
  if (diff.includes('med') || diff.includes('medium')) return 'Medium'
  if (diff.includes('hard')) return 'Hard'
  return difficulty
}

/**
 * URL 제목을 생성합니다.
 * @param {string} title - 원본 제목
 * @returns {string} URL용 제목
 */
export function generateUrlTitle(title) {
  return title
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .trim()
}

/**
 * LeetCode 문제 텍스트를 파싱합니다.
 * @param {string} leetcodeProblems - 파싱할 텍스트
 * @returns {Array} 파싱된 문제 배열
 */
export function parseLeetCodeProblems(leetcodeProblems) {
  const problems = []
  
  if (!leetcodeProblems.trim()) {
    return problems
  }
  
  const lines = leetcodeProblems.trim().split('\n')
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim()
    if (!line) continue
    
    // LeetCode 문제 형식 파싱: "146. LRU Cache\n45.9%\nMed."
    const problemMatch = line.match(/^(\d+)\.\s+(.+)$/)
    if (problemMatch) {
      const number = parseInt(problemMatch[1])
      const title = problemMatch[2].trim()
      
      // 다음 줄들에서 난이도와 URL 찾기
      let difficulty = null
      let url = null
      
      for (let j = i + 1; j < Math.min(i + 4, lines.length); j++) {
        const nextLine = lines[j].trim()
        if (!nextLine) continue
        
        // URL 찾기 (@https://...)
        const urlMatch = nextLine.match(/@(https?:\/\/[^\s]+)/)
        if (urlMatch && !url) {
          url = urlMatch[1]
          continue
        }
        
        // 난이도 찾기 (Easy, Med., Hard) - 더 유연한 패턴
        const difficultyMatch = nextLine.match(/(Easy|Med\.?|Medium|Hard)/i)
        if (difficultyMatch && difficulty === null) {
          difficulty = normalizeDifficulty(difficultyMatch[1])
          continue
        }
      }
      
      const problem = {
        id: number,
        title,
        difficulty: difficulty || 'Unknown',
        error: null
      }
      
      // URL 설정
      if (url) {
        problem.url = url
      } else {
        // URL이 없으면 기본 URL 생성
        const urlTitle = generateUrlTitle(title)
        problem.url = `https://leetcode.com/problems/${urlTitle}/`
      }
      
      problem.acceptance_rate = 0 // 정답률은 파싱하지 않음
      
      problems.push(problem)
    }
  }
  
  return problems
}

/**
 * 문제 데이터를 시험에 추가할 형식으로 변환합니다.
 * @param {Object} problem - 파싱된 문제 객체
 * @returns {Object} 시험에 추가할 문제 데이터
 */
export function convertToQuestionData(problem) {
  return {
    csv_id: problem.id.toString(),
    title: problem.title,
    content: problem.title,
    answer: 'Y',
    difficulty: problem.difficulty === 'Unknown' ? 'unknown' : problem.difficulty.toLowerCase(),
    url: problem.url
  }
}
