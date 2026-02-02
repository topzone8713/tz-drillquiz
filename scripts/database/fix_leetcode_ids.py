#!/usr/bin/env python
"""
잘못된 LeetCode ID를 올바른 ID로 수정하는 스크립트
"""

import psycopg2
from psycopg2.extras import RealDictCursor

def connect_to_database():
    """데이터베이스에 연결합니다."""
    db_config = {
        'host': 'localhost',
        'port': 58295,
        'database': 'drillquiz',
        'user': 'admin',
        'password': 'DevOps!323'
    }
    
    try:
        print(f"데이터베이스 연결: {db_config['host']}:{db_config['port']}")
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        return conn, cursor
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return None, None

def get_correct_leetcode_mapping():
    """올바른 LeetCode 문제 ID 매핑을 반환합니다."""
    return {
        # 문제 제목 -> 올바른 LeetCode ID
        "388. Longest Absolute File Path": "388",
        "934. Shortest Bridge": "934", 
        "523. Continuous Subarray Sum": "523",
        "721. Accounts Merge": "721",
        "78. Subsets": "78",
        "691. Stickers to Spell Word": "691",
        "398. Random Pick Index": "398",
        "636. Exclusive Time of Functions": "636",
        "249. Group Shifted Strings": "249",
        "729. My Calendar I": "729",
        "79. Word Search": "79",
        "974. Subarray Sums Divisible by K": "974",
        "84. Largest Rectangle in Histogram": "84",
        "545. Boundary of Binary Tree": "545",
        "973. K Closest Points to Origin": "973",
        "88. Merge Sorted Array": "88",
        "863. All Nodes Distance K in Binary Tree": "863",
        "76. Minimum Window Substring": "76",
        "48. Rotate Image": "48",
        "14. Longest Common Prefix": "14",
        "35. Search Insert Position": "35",
        "3356. Zero Array Transformation II": "3356",
        "987. Vertical Order Traversal of a Binary Tree": "987",
        "986. Interval List Intersections": "986",
        "791. Custom Sort String": "791",
        "560. Subarray Sum Equals K": "560",
        "528. Random Pick with Weight": "528",
        "465. Optimal Account Balancing": "465",
        "399. Evaluate Division": "399",
        "1492. The kth Factor of n": "1492",
        "122. Best Time to Buy and Sell Stock II": "122",
        "33. Search in Rotated Sorted Array": "33",
        "994. Rotting Oranges": "994",
        "977. Squares of a Sorted Array": "977",
        "71. Simplify Path": "71",
        "564. Find the Closest Palindrome": "564",
        "55. Jump Game": "55",
        "50. Pow(x, n)": "50",
        "380. Insert Delete GetRandom O(1)": "380",
        "3351. Sum of Good Subsequences": "3351",
        "3342. Find Minimum Time to Reach Last Room II": "3342",
        "54. Spiral Matrix": "54",
        "42. Trapping Rain Water": "42",
        "939. Minimum Area Rectangle": "939",
        "938. Range Sum of BST": "938",
        "921. Minimum Add to Make Parentheses Valid": "921",
        "70. Climbing Stairs": "70",
        "56. Merge Intervals": "56",
        "53. Maximum Subarray": "53",
        "31. Next Permutation": "31",
        "305. Number of Islands II": "305",
        "543. Diameter of Binary Tree": "543",
        "236. Lowest Common Ancestor of a Binary Tree": "236",
        "215. Kth Largest Element in an Array": "215",
        "9. Palindrome Number": "9",
        "767. Reorganize String": "767",
        "680. Valid Palindrome II": "680",
        "670. Maximum Swap": "670",
        "4. Median of Two Sorted Arrays": "4",
        "3161. Block Placement Queries": "3161",
        "199. Binary Tree Right Side View": "199",
        "815. Bus Routes": "815",
        "7. Reverse Integer": "7",
        "621. Task Scheduler": "621",
        "5. Longest Palindromic Substring": "5",
        "426. Convert Binary Search Tree to Sorted Doubly Linked List": "426",
        "408. Valid Word Abbreviation": "408",
        "362. Design Hit Counter": "362",
        "3. Longest Substring Without Repeating Characters": "3",
        "269. Alien Dictionary": "269",
        "1768. Merge Strings Alternately": "1768",
        "36. Valid Sudoku": "36",
        "359. Logger Rate Limiter": "359",
        "347. Top K Frequent Elements": "347",
        "346. Moving Average from Data Stream": "346",
        "3404. Count Special Subsequences": "3404",
        "34. Find First and Last Position of Element in Sorted Array": "34",
        "2667. Create Hello World Function": "2667",
        "253. Meeting Rooms II": "253",
        "2468. Split Message Based on Limit": "2468",
        "1757. Recyclable and Low Fat Products": "1757",
        "68. Text Justification": "68",
        "49. Group Anagrams": "49",
        "339. Nested List Weight Sum": "339",
        "3387. Maximize Amount After Two Days of Conversions": "3387",
        "3371. Identify the Largest Outlier in an Array": "3371",
        "3355. Zero Array Transformation I": "3355",
        "300. Longest Increasing Subsequence": "300",
        "295. Find Median from Data Stream": "295",
        "20. Valid Parentheses": "20",
        "1762. Buildings With an Ocean View": "1762",
        "427. Construct Quad Tree": "427",
        "3366. Minimum Array Sum": "3366",
        "314. Binary Tree Vertical Order Traversal": "314",
        "28. Find the Index of the First Occurrence in a String": "28",
        "270. Closest Binary Search Tree Value": "270",
        "2663. Lexicographically Smallest Beautiful String": "2663",
        "2444. Count Subarrays With Fixed Bounds": "2444",
        "227. Basic Calculator II": "227",
        "200. Number of Islands": "200",
        "1650. Lowest Common Ancestor of a Binary Tree III": "1650",
        "3341. Find Minimum Time to Reach Last Room I": "3341",
        "27. Remove Element": "27",
        "26. Remove Duplicates from Sorted Array": "26",
        "2502. Design Memory Allocator": "2502",
        "238. Product of Array Except Self": "238",
        "230. Kth Smallest Element in a BST": "230",
        "23. Merge k Sorted Lists": "23",
        "2235. Add Two Integers": "2235",
        "2. Add Two Numbers": "2",
        "163. Missing Ranges": "163",
        "2337. Move Pieces to Obtain a String": "2337",
        "22. Generate Parentheses": "22",
        "206. Reverse Linked List": "206",
        "224. Basic Calculator": "224",
        "2115. Find All Possible Recipes from Given Supplies": "2115",
        "210. Course Schedule II": "210",
        "17. Letter Combinations of a Phone Number": "17",
        "162. Find Peak Element": "162",
        "1539. Kth Missing Positive Number": "1539",
        "133. Clone Graph": "133",
        "588. Design In-Memory File System": "588",
        "212. Word Search II": "212",
        "207. Course Schedule": "207",
        "198. House Robber": "198",
        "169. Majority Element": "169",
        "1570. Dot Product of Two Sparse Vectors": "1570",
        "15. 3Sum": "15",
        "139. Word Break": "139",
        "136. Single Number": "136",
        "1249. Minimum Remove to Make Valid Parentheses": "1249",
        "827. Making A Large Island": "827",
        "1526. Minimum Number of Increments on Subarrays to Form a Target Array": "1526",
        "146. LRU Cache": "146",
        "1438. Longest Continuous Subarray With Absolute Diff Less Than or Equal to Limit": "1438",
        "138. Copy List with Random Pointer": "138",
        "13. Roman to Integer": "13",
        "129. Sum Root to Leaf Numbers": "129",
        "128. Longest Consecutive Sequence": "128",
        "118. Pascal's Triangle": "118",
        "1091. Shortest Path in Binary Matrix": "1091",
        "65. Valid Number": "65",
        "127. Word Ladder": "127",
        "125. Valid Palindrome": "125",
        "1229. Meeting Scheduler": "1229",
        "121. Best Time to Buy and Sell Stock": "121",
        "1152. Analyze User Website Visit Pattern": "1152",
        "1101. The Earliest Moment When Everyone Become Friends": "1101",
        "11. Container With Most Water": "11",
        "1004. Max Consecutive Ones III": "1004",
        "1. Two Sum": "1",
        
        # 숫자 없이 제목만 있는 경우들도 추가
        "Longest Absolute File Path": "388",
        "Shortest Bridge": "934", 
        "Continuous Subarray Sum": "523",
        "Accounts Merge": "721",
        "Subsets": "78",
        "Stickers to Spell Word": "691",
        "Random Pick Index": "398",
        "Exclusive Time of Functions": "636",
        "Group Shifted Strings": "249",
        "My Calendar I": "729",
        "Word Search": "79",
        "Subarray Sums Divisible by K": "974",
        "Largest Rectangle in Histogram": "84",
        "Boundary of Binary Tree": "545",
        "K Closest Points to Origin": "973",
        "Merge Sorted Array": "88",
        "All Nodes Distance K in Binary Tree": "863",
        "Minimum Window Substring": "76",
        "Rotate Image": "48",
        "Longest Common Prefix": "14",
        "Search Insert Position": "35",
        "Zero Array Transformation II": "3356",
        "Vertical Order Traversal of a Binary Tree": "987",
        "Interval List Intersections": "986",
        "Custom Sort String": "791",
        "Subarray Sum Equals K": "560",
        "Random Pick with Weight": "528",
        "Optimal Account Balancing": "465",
        "Evaluate Division": "399",
        "The kth Factor of n": "1492",
        "Best Time to Buy and Sell Stock II": "122",
        "Search in Rotated Sorted Array": "33",
        "Rotting Oranges": "994",
        "Squares of a Sorted Array": "977",
        "Simplify Path": "71",
        "Find the Closest Palindrome": "564",
        "Jump Game": "55",
        "Pow(x, n)": "50",
        "Insert Delete GetRandom O(1)": "380",
        "Sum of Good Subsequences": "3351",
        "Find Minimum Time to Reach Last Room II": "3342",
        "Spiral Matrix": "54",
        "Trapping Rain Water": "42",
        "Minimum Area Rectangle": "939",
        "Range Sum of BST": "938",
        "Minimum Add to Make Parentheses Valid": "921",
        "Climbing Stairs": "70",
        "Merge Intervals": "56",
        "Maximum Subarray": "53",
        "Next Permutation": "31",
        "Number of Islands II": "305",
        "Diameter of Binary Tree": "543",
        "Lowest Common Ancestor of a Binary Tree": "236",
        "Kth Largest Element in an Array": "215",
        "Palindrome Number": "9",
        "Reorganize String": "767",
        "Valid Palindrome II": "680",
        "Maximum Swap": "670",
        "Median of Two Sorted Arrays": "4",
        "Block Placement Queries": "3161",
        "Binary Tree Right Side View": "199",
        "Bus Routes": "815",
        "Reverse Integer": "7",
        "Task Scheduler": "621",
        "Longest Palindromic Substring": "5",
        "Convert Binary Search Tree to Sorted Doubly Linked List": "426",
        "Valid Word Abbreviation": "408",
        "Design Hit Counter": "362",
        "Longest Substring Without Repeating Characters": "3",
        "Alien Dictionary": "269",
        "Merge Strings Alternately": "1768",
        "Valid Sudoku": "36",
        "Logger Rate Limiter": "359",
        "Top K Frequent Elements": "347",
        "Moving Average from Data Stream": "346",
        "Count Special Subsequences": "3404",
        "Find First and Last Position of Element in Sorted Array": "34",
        "Create Hello World Function": "2667",
        "Meeting Rooms II": "253",
        "Split Message Based on Limit": "2468",
        "Recyclable and Low Fat Products": "1757",
        "Text Justification": "68",
        "Group Anagrams": "49",
        "Nested List Weight Sum": "339",
        "Maximize Amount After Two Days of Conversions": "3387",
        "Identify the Largest Outlier in an Array": "3371",
        "Zero Array Transformation I": "3355",
        "Longest Increasing Subsequence": "300",
        "Find Median from Data Stream": "295",
        "Valid Parentheses": "20",
        "Buildings With an Ocean View": "1762",
        "Construct Quad Tree": "427",
        "Minimum Array Sum": "3366",
        "Binary Tree Vertical Order Traversal": "314",
        "Find the Index of the First Occurrence in a String": "28",
        "Closest Binary Search Tree Value": "270",
        "Lexicographically Smallest Beautiful String": "2663",
        "Count Subarrays With Fixed Bounds": "2444",
        "Basic Calculator II": "227",
        "Number of Islands": "200",
        "Lowest Common Ancestor of a Binary Tree III": "1650",
        "Find Minimum Time to Reach Last Room I": "3341",
        "Remove Element": "27",
        "Remove Duplicates from Sorted Array": "26",
        "Design Memory Allocator": "2502",
        "Product of Array Except Self": "238",
        "Kth Smallest Element in a BST": "230",
        "Merge k Sorted Lists": "23",
        "Add Two Integers": "2235",
        "Add Two Numbers": "2",
        "Missing Ranges": "163",
        "Move Pieces to Obtain a String": "2337",
        "Generate Parentheses": "22",
        "Reverse Linked List": "206",
        "Basic Calculator": "224",
        "Find All Possible Recipes from Given Supplies": "2115",
        "Course Schedule II": "210",
        "Letter Combinations of a Phone Number": "17",
        "Find Peak Element": "162",
        "Kth Missing Positive Number": "1539",
        "Clone Graph": "133",
        "Design In-Memory File System": "588",
        "Word Search II": "212",
        "Course Schedule": "207",
        "House Robber": "198",
        "Majority Element": "169",
        "Dot Product of Two Sparse Vectors": "1570",
        "3Sum": "15",
        "Word Break": "139",
        "Single Number": "136",
        "Minimum Remove to Make Valid Parentheses": "1249",
        "Making A Large Island": "827",
        "Minimum Number of Increments on Subarrays to Form a Target Array": "1526",
        "LRU Cache": "146",
        "Longest Continuous Subarray With Absolute Diff Less Than or Equal to Limit": "1438",
        "Copy List with Random Pointer": "138",
        "Roman to Integer": "13",
        "Sum Root to Leaf Numbers": "129",
        "Longest Consecutive Sequence": "128",
        "Pascal's Triangle": "118",
        "Shortest Path in Binary Matrix": "1091",
        "Valid Number": "65",
        "Word Ladder": "127",
        "Valid Palindrome": "125",
        "Meeting Scheduler": "1229",
        "Best Time to Buy and Sell Stock": "121",
        "Analyze User Website Visit Pattern": "1152",
        "The Earliest Moment When Everyone Become Friends": "1101",
        "Container With Most Water": "11",
        "Max Consecutive Ones III": "1004",
        "Two Sum": "1"
    }

def find_wrong_leetcode_ids(cursor):
    """잘못된 LeetCode ID를 가진 문제들을 찾습니다."""
    print("\n=== 잘못된 LeetCode ID 찾기 ===")
    
    correct_mapping = get_correct_leetcode_mapping()
    wrong_ids = []
    
    # 각 문제 제목에 대해 올바른 ID와 현재 ID를 비교
    for title, correct_id in correct_mapping.items():
        cursor.execute("""
            SELECT id, title_en, csv_id 
            FROM quiz_question 
            WHERE title_en = %s AND csv_id != %s
        """, (title, correct_id))
        
        wrong_questions = cursor.fetchall()
        if wrong_questions:
            for question in wrong_questions:
                wrong_ids.append({
                    'id': question['id'],
                    'title': question['title_en'],
                    'current_id': question['csv_id'],
                    'correct_id': correct_id
                })
    
    print(f"잘못된 ID를 가진 문제 수: {len(wrong_ids)}")
    return wrong_ids

def fix_leetcode_ids(cursor, conn):
    """잘못된 LeetCode ID를 올바른 ID로 수정합니다."""
    print("\n=== LeetCode ID 수정 시작 ===")
    
    wrong_questions = find_wrong_leetcode_ids(cursor)
    updated_count = 0
    
    for question in wrong_questions:
        try:
            # CSV ID 업데이트
            cursor.execute("""
                UPDATE quiz_question 
                SET csv_id = %s, updated_at = NOW()
                WHERE id = %s
            """, (question['correct_id'], question['id']))
            
            print(f"✅ {question['title']}: {question['current_id']} → {question['correct_id']}")
            updated_count += 1
            
        except Exception as e:
            print(f"❌ {question['title']}: 업데이트 실패 - {e}")
    
    # 변경사항 커밋
    try:
        conn.commit()
        print(f"\n✅ 총 {updated_count}개 문제의 ID가 수정되었습니다.")
        return updated_count
    except Exception as e:
        print(f"\n❌ 커밋 실패: {e}")
        conn.rollback()
        return 0

def verify_fixes(cursor):
    """수정 결과를 확인합니다."""
    print("\n=== 수정 결과 확인 ===")
    
    # 수정 후 잘못된 ID가 남아있는지 확인
    wrong_questions = find_wrong_leetcode_ids(cursor)
    
    if len(wrong_questions) == 0:
        print("✅ 모든 LeetCode ID가 올바르게 수정되었습니다!")
    else:
        print(f"⚠️  여전히 {len(wrong_questions)}개의 잘못된 ID가 남아있습니다.")
        for question in wrong_questions[:5]:  # 처음 5개만 출력
            print(f"  - {question['title']}: {question['current_id']} (올바른 ID: {question['correct_id']})")

def main():
    """메인 함수"""
    print("=== LeetCode ID 수정 스크립트 ===")
    
    # 데이터베이스 연결
    conn, cursor = connect_to_database()
    if not conn or not cursor:
        return
    
    try:
        # LeetCode ID 수정
        updated_count = fix_leetcode_ids(cursor, conn)
        
        if updated_count > 0:
            # 수정 결과 확인
            verify_fixes(cursor)
        
        print("\n=== 작업 완료 ===")
        
    except Exception as e:
        print(f"\n❌ 작업 중 오류 발생: {e}")
        conn.rollback()
    
    finally:
        cursor.close()
        conn.close()
        print("데이터베이스 연결을 종료했습니다.")

if __name__ == "__main__":
    main()











