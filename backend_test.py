#!/usr/bin/env python3
"""Comprehensive backend test for Admin/SEO management endpoints"""
import requests
import json
import sys

BASE_URL = "https://45ca9796-e5fd-4358-a4b3-f57a860064e7.preview.emergentagent.com/api"
ADMIN_EMAIL = "admin@lovepdf.com"
ADMIN_PASSWORD = "Admin@12345"

# Test results tracking
results = []

def test(name, passed, status_code=None, details=""):
    """Record test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    result = f"{status} | {name}"
    if status_code:
        result += f" | HTTP {status_code}"
    if details:
        result += f" | {details}"
    results.append((passed, result))
    print(result)
    return passed

def print_summary():
    """Print test summary table"""
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    passed = sum(1 for p, _ in results if p)
    total = len(results)
    print(f"Total: {passed}/{total} passed")
    print("="*80)
    for _, result in results:
        print(result)
    print("="*80)

# ============================================================================
# TEST 1: Authentication
# ============================================================================
print("\n### TEST 1: Authentication ###")

# 1a. Login with correct credentials
try:
    resp = requests.post(f"{BASE_URL}/admin/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }, timeout=10)
    
    if resp.status_code == 200 and "access_token" in resp.json():
        ACCESS_TOKEN = resp.json()["access_token"]
        test("1a. Login with correct credentials", True, resp.status_code, f"Got access_token")
    else:
        test("1a. Login with correct credentials", False, resp.status_code, f"Response: {resp.text[:200]}")
        sys.exit(1)
except Exception as e:
    test("1a. Login with correct credentials", False, details=f"Exception: {e}")
    sys.exit(1)

# 1b. Login with wrong password
try:
    resp = requests.post(f"{BASE_URL}/admin/login", json={
        "email": ADMIN_EMAIL,
        "password": "WrongPassword123"
    }, timeout=10)
    test("1b. Login with wrong password -> 401", resp.status_code == 401, resp.status_code, f"Response: {resp.text[:100]}")
except Exception as e:
    test("1b. Login with wrong password -> 401", False, details=f"Exception: {e}")

# ============================================================================
# TEST 2: GET /api/admin/me
# ============================================================================
print("\n### TEST 2: GET /api/admin/me ###")

# 2a. With valid token
try:
    resp = requests.get(f"{BASE_URL}/admin/me", headers={
        "Authorization": f"Bearer {ACCESS_TOKEN}"
    }, timeout=10)
    
    if resp.status_code == 200 and resp.json().get("email") == ADMIN_EMAIL:
        test("2a. GET /admin/me with valid token -> 200", True, resp.status_code, f"Email: {resp.json().get('email')}")
    else:
        test("2a. GET /admin/me with valid token -> 200", False, resp.status_code, f"Response: {resp.text[:200]}")
except Exception as e:
    test("2a. GET /admin/me with valid token -> 200", False, details=f"Exception: {e}")

# 2b. Without Authorization header
try:
    resp = requests.get(f"{BASE_URL}/admin/me", timeout=10)
    test("2b. GET /admin/me without token -> 401", resp.status_code == 401, resp.status_code)
except Exception as e:
    test("2b. GET /admin/me without token -> 401", False, details=f"Exception: {e}")

# 2c. With garbage token
try:
    resp = requests.get(f"{BASE_URL}/admin/me", headers={
        "Authorization": "Bearer garbage_token_12345"
    }, timeout=10)
    test("2c. GET /admin/me with garbage token -> 401", resp.status_code == 401, resp.status_code)
except Exception as e:
    test("2c. GET /admin/me with garbage token -> 401", False, details=f"Exception: {e}")

# ============================================================================
# TEST 3: SEO Pages
# ============================================================================
print("\n### TEST 3: SEO Pages ###")

# 3a. PUT /api/admin/seo/pages with auth
try:
    resp = requests.put(f"{BASE_URL}/admin/seo/pages", 
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
        json={
            "path": "/tool/merge-pdf",
            "title": "Merge PDF Free",
            "description": "Combine PDFs online",
            "keywords": "merge pdf"
        }, timeout=10)
    test("3a. PUT /admin/seo/pages with auth -> 200", resp.status_code == 200, resp.status_code, f"Response: {resp.text[:100]}")
except Exception as e:
    test("3a. PUT /admin/seo/pages with auth -> 200", False, details=f"Exception: {e}")

# 3b. GET /api/seo/page?path=/tool/merge-pdf (public, no auth)
try:
    resp = requests.get(f"{BASE_URL}/seo/page?path=/tool/merge-pdf", timeout=10)
    
    if resp.status_code == 200:
        seo_data = resp.json().get("seo", {})
        if seo_data and seo_data.get("title") == "Merge PDF Free":
            test("3b. GET /seo/page (public) returns stored SEO", True, resp.status_code, f"Title: {seo_data.get('title')}")
        else:
            test("3b. GET /seo/page (public) returns stored SEO", False, resp.status_code, f"SEO data: {seo_data}")
    else:
        test("3b. GET /seo/page (public) returns stored SEO", False, resp.status_code, f"Response: {resp.text[:200]}")
except Exception as e:
    test("3b. GET /seo/page (public) returns stored SEO", False, details=f"Exception: {e}")

# 3c. GET /api/admin/seo/pages (auth) lists it
try:
    resp = requests.get(f"{BASE_URL}/admin/seo/pages", 
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}, timeout=10)
    
    if resp.status_code == 200:
        pages = resp.json().get("pages", [])
        merge_pdf_page = next((p for p in pages if p.get("path") == "/tool/merge-pdf"), None)
        if merge_pdf_page:
            test("3c. GET /admin/seo/pages lists the page", True, resp.status_code, f"Found {len(pages)} pages")
        else:
            test("3c. GET /admin/seo/pages lists the page", False, resp.status_code, f"merge-pdf page not found in {len(pages)} pages")
    else:
        test("3c. GET /admin/seo/pages lists the page", False, resp.status_code, f"Response: {resp.text[:200]}")
except Exception as e:
    test("3c. GET /admin/seo/pages lists the page", False, details=f"Exception: {e}")

# 3d. PUT without token -> 401
try:
    resp = requests.put(f"{BASE_URL}/admin/seo/pages", json={
        "path": "/tool/test",
        "title": "Test"
    }, timeout=10)
    test("3d. PUT /admin/seo/pages without token -> 401", resp.status_code == 401, resp.status_code)
except Exception as e:
    test("3d. PUT /admin/seo/pages without token -> 401", False, details=f"Exception: {e}")

# ============================================================================
# TEST 4: Site Settings
# ============================================================================
print("\n### TEST 4: Site Settings ###")

# 4a. PUT /api/admin/site with auth
try:
    resp = requests.put(f"{BASE_URL}/admin/site",
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
        json={
            "site_name": "LovePDF",
            "site_url": "https://example.com",
            "ga_measurement_id": "G-TEST123",
            "gsc_verification": "verifycode",
            "organization_name": "LovePDF"
        }, timeout=10)
    test("4a. PUT /admin/site with auth -> 200", resp.status_code == 200, resp.status_code, f"Response: {resp.text[:100]}")
except Exception as e:
    test("4a. PUT /admin/site with auth -> 200", False, details=f"Exception: {e}")

# 4b. GET /api/seo/site (public) reflects ga_measurement_id
try:
    resp = requests.get(f"{BASE_URL}/seo/site", timeout=10)
    
    if resp.status_code == 200:
        site_data = resp.json().get("site", {})
        if site_data.get("ga_measurement_id") == "G-TEST123":
            test("4b. GET /seo/site (public) reflects ga_measurement_id", True, resp.status_code, f"GA ID: {site_data.get('ga_measurement_id')}")
        else:
            test("4b. GET /seo/site (public) reflects ga_measurement_id", False, resp.status_code, f"GA ID: {site_data.get('ga_measurement_id')}")
    else:
        test("4b. GET /seo/site (public) reflects ga_measurement_id", False, resp.status_code, f"Response: {resp.text[:200]}")
except Exception as e:
    test("4b. GET /seo/site (public) reflects ga_measurement_id", False, details=f"Exception: {e}")

# ============================================================================
# TEST 5: Blog CRUD
# ============================================================================
print("\n### TEST 5: Blog CRUD ###")

# 5a. POST /api/admin/blog (published post)
try:
    resp = requests.post(f"{BASE_URL}/admin/blog",
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
        json={
            "slug": "how-to-merge-pdf",
            "title": "How to merge PDF",
            "excerpt": "Learn how to merge PDFs easily",
            "content": "<p>hi</p>",
            "published": True
        }, timeout=10)
    
    if resp.status_code == 200 and "id" in resp.json():
        BLOG_POST_ID = resp.json()["id"]
        test("5a. POST /admin/blog (published) -> 200 with id", True, resp.status_code, f"ID: {BLOG_POST_ID}")
    else:
        test("5a. POST /admin/blog (published) -> 200 with id", False, resp.status_code, f"Response: {resp.text[:200]}")
        BLOG_POST_ID = None
except Exception as e:
    test("5a. POST /admin/blog (published) -> 200 with id", False, details=f"Exception: {e}")
    BLOG_POST_ID = None

# 5b. GET /api/blog (public) lists the post
try:
    resp = requests.get(f"{BASE_URL}/blog", timeout=10)
    
    if resp.status_code == 200:
        posts = resp.json().get("posts", [])
        merge_post = next((p for p in posts if p.get("slug") == "how-to-merge-pdf"), None)
        if merge_post:
            test("5b. GET /blog (public) lists the post", True, resp.status_code, f"Found post with slug 'how-to-merge-pdf'")
        else:
            test("5b. GET /blog (public) lists the post", False, resp.status_code, f"Post not found in {len(posts)} posts")
    else:
        test("5b. GET /blog (public) lists the post", False, resp.status_code, f"Response: {resp.text[:200]}")
except Exception as e:
    test("5b. GET /blog (public) lists the post", False, details=f"Exception: {e}")

# 5c. GET /api/blog/how-to-merge-pdf (public) returns full post
try:
    resp = requests.get(f"{BASE_URL}/blog/how-to-merge-pdf", timeout=10)
    
    if resp.status_code == 200:
        post = resp.json().get("post", {})
        if post.get("content") == "<p>hi</p>":
            test("5c. GET /blog/{slug} (public) returns full post", True, resp.status_code, f"Content: {post.get('content')}")
        else:
            test("5c. GET /blog/{slug} (public) returns full post", False, resp.status_code, f"Content: {post.get('content')}")
    else:
        test("5c. GET /blog/{slug} (public) returns full post", False, resp.status_code, f"Response: {resp.text[:200]}")
except Exception as e:
    test("5c. GET /blog/{slug} (public) returns full post", False, details=f"Exception: {e}")

# 5d. POST same slug again -> 400
try:
    resp = requests.post(f"{BASE_URL}/admin/blog",
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
        json={
            "slug": "how-to-merge-pdf",
            "title": "Duplicate",
            "published": True
        }, timeout=10)
    test("5d. POST duplicate slug -> 400", resp.status_code == 400, resp.status_code, f"Response: {resp.text[:100]}")
except Exception as e:
    test("5d. POST duplicate slug -> 400", False, details=f"Exception: {e}")

# 5e. PUT /api/admin/blog/{id} change title
if BLOG_POST_ID:
    try:
        resp = requests.put(f"{BASE_URL}/admin/blog/{BLOG_POST_ID}",
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
            json={
                "slug": "how-to-merge-pdf",
                "title": "How to merge PDF - Updated",
                "excerpt": "Learn how to merge PDFs easily",
                "content": "<p>hi</p>",
                "published": True
            }, timeout=10)
        test("5e. PUT /admin/blog/{id} change title -> 200", resp.status_code == 200, resp.status_code, f"Response: {resp.text[:100]}")
    except Exception as e:
        test("5e. PUT /admin/blog/{id} change title -> 200", False, details=f"Exception: {e}")
else:
    test("5e. PUT /admin/blog/{id} change title -> 200", False, details="Skipped - no blog post ID")

# 5f. GET /api/blog/how-to-merge-pdf reflects new title
try:
    resp = requests.get(f"{BASE_URL}/blog/how-to-merge-pdf", timeout=10)
    
    if resp.status_code == 200:
        post = resp.json().get("post", {})
        if post.get("title") == "How to merge PDF - Updated":
            test("5f. GET /blog/{slug} reflects new title", True, resp.status_code, f"Title: {post.get('title')}")
        else:
            test("5f. GET /blog/{slug} reflects new title", False, resp.status_code, f"Title: {post.get('title')}")
    else:
        test("5f. GET /blog/{slug} reflects new title", False, resp.status_code, f"Response: {resp.text[:200]}")
except Exception as e:
    test("5f. GET /blog/{slug} reflects new title", False, details=f"Exception: {e}")

# 5g. Create unpublished post
try:
    resp = requests.post(f"{BASE_URL}/admin/blog",
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
        json={
            "slug": "unpublished-draft",
            "title": "Draft Post",
            "published": False
        }, timeout=10)
    
    if resp.status_code == 200:
        UNPUBLISHED_ID = resp.json().get("id")
        test("5g. POST unpublished post -> 200", True, resp.status_code, f"ID: {UNPUBLISHED_ID}")
    else:
        test("5g. POST unpublished post -> 200", False, resp.status_code, f"Response: {resp.text[:200]}")
        UNPUBLISHED_ID = None
except Exception as e:
    test("5g. POST unpublished post -> 200", False, details=f"Exception: {e}")
    UNPUBLISHED_ID = None

# 5h. Unpublished post does NOT appear in GET /api/blog
try:
    resp = requests.get(f"{BASE_URL}/blog", timeout=10)
    
    if resp.status_code == 200:
        posts = resp.json().get("posts", [])
        draft_post = next((p for p in posts if p.get("slug") == "unpublished-draft"), None)
        if not draft_post:
            test("5h. Unpublished post NOT in GET /blog", True, resp.status_code, "Draft correctly hidden")
        else:
            test("5h. Unpublished post NOT in GET /blog", False, resp.status_code, "Draft post visible in public list")
    else:
        test("5h. Unpublished post NOT in GET /blog", False, resp.status_code, f"Response: {resp.text[:200]}")
except Exception as e:
    test("5h. Unpublished post NOT in GET /blog", False, details=f"Exception: {e}")

# 5i. GET /api/blog/unpublished-draft -> 404
try:
    resp = requests.get(f"{BASE_URL}/blog/unpublished-draft", timeout=10)
    test("5i. GET /blog/{unpublished-slug} -> 404", resp.status_code == 404, resp.status_code)
except Exception as e:
    test("5i. GET /blog/{unpublished-slug} -> 404", False, details=f"Exception: {e}")

# 5j. DELETE /api/admin/blog/{id} -> 200
if BLOG_POST_ID:
    try:
        resp = requests.delete(f"{BASE_URL}/admin/blog/{BLOG_POST_ID}",
            headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}, timeout=10)
        test("5j. DELETE /admin/blog/{id} -> 200", resp.status_code == 200, resp.status_code, f"Response: {resp.text[:100]}")
    except Exception as e:
        test("5j. DELETE /admin/blog/{id} -> 200", False, details=f"Exception: {e}")
else:
    test("5j. DELETE /admin/blog/{id} -> 200", False, details="Skipped - no blog post ID")

# 5k. DELETE non-existent id -> 404
try:
    resp = requests.delete(f"{BASE_URL}/admin/blog/non-existent-id-12345",
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"}, timeout=10)
    test("5k. DELETE non-existent blog id -> 404", resp.status_code == 404, resp.status_code)
except Exception as e:
    test("5k. DELETE non-existent blog id -> 404", False, details=f"Exception: {e}")

# ============================================================================
# TEST 6: Sitemap & Robots
# ============================================================================
print("\n### TEST 6: Sitemap & Robots ###")

# 6a. GET /api/sitemap.xml
try:
    resp = requests.get(f"{BASE_URL}/sitemap.xml", timeout=10)
    
    if resp.status_code == 200:
        content_type = resp.headers.get("content-type", "")
        body = resp.text
        
        # Check content type
        is_xml = "xml" in content_type.lower()
        
        # Check for valid XML structure
        has_xml_declaration = '<?xml' in body
        has_urlset = '<urlset' in body
        
        # Check for specific URLs
        has_merge_pdf = '<loc>https://example.com/tool/merge-pdf</loc>' in body
        
        # Check for blog post (we deleted the published one, but check structure)
        has_blog_section = '/blog/' in body or '<loc>https://example.com/blog</loc>' in body
        
        # Check that site_url is used (https://example.com from step 4)
        uses_site_url = 'https://example.com' in body
        
        all_checks = is_xml and has_xml_declaration and has_urlset and has_merge_pdf and uses_site_url
        
        details = f"Content-Type: {content_type}, XML: {has_xml_declaration}, URLset: {has_urlset}, merge-pdf: {has_merge_pdf}, site_url: {uses_site_url}"
        test("6a. GET /sitemap.xml -> 200, valid XML with tool URLs", all_checks, resp.status_code, details)
        
        if not all_checks:
            print(f"   Sitemap body preview: {body[:500]}")
    else:
        test("6a. GET /sitemap.xml -> 200, valid XML with tool URLs", False, resp.status_code, f"Response: {resp.text[:200]}")
except Exception as e:
    test("6a. GET /sitemap.xml -> 200, valid XML with tool URLs", False, details=f"Exception: {e}")

# 6b. GET /api/robots.txt
try:
    resp = requests.get(f"{BASE_URL}/robots.txt", timeout=10)
    
    if resp.status_code == 200:
        content_type = resp.headers.get("content-type", "")
        body = resp.text
        
        is_text = "text" in content_type.lower()
        has_disallow_admin = "Disallow: /admin" in body
        has_sitemap = "Sitemap:" in body
        
        all_checks = is_text and has_disallow_admin and has_sitemap
        
        details = f"Content-Type: {content_type}, Disallow /admin: {has_disallow_admin}, Sitemap line: {has_sitemap}"
        test("6b. GET /robots.txt -> 200, contains Disallow /admin and Sitemap", all_checks, resp.status_code, details)
        
        if not all_checks:
            print(f"   Robots.txt body: {body}")
    else:
        test("6b. GET /robots.txt -> 200, contains Disallow /admin and Sitemap", False, resp.status_code, f"Response: {resp.text[:200]}")
except Exception as e:
    test("6b. GET /robots.txt -> 200, contains Disallow /admin and Sitemap", False, details=f"Exception: {e}")

# ============================================================================
# TEST 7: Change Password
# ============================================================================
print("\n### TEST 7: Change Password ###")

# 7a. POST /api/admin/change-password with correct current password
try:
    resp = requests.post(f"{BASE_URL}/admin/change-password",
        headers={"Authorization": f"Bearer {ACCESS_TOKEN}"},
        json={
            "current_password": ADMIN_PASSWORD,
            "new_password": "NewPass@999"
        }, timeout=10)
    test("7a. POST /admin/change-password -> 200", resp.status_code == 200, resp.status_code, f"Response: {resp.text[:100]}")
except Exception as e:
    test("7a. POST /admin/change-password -> 200", False, details=f"Exception: {e}")

# 7b. Login with new password -> 200
try:
    resp = requests.post(f"{BASE_URL}/admin/login", json={
        "email": ADMIN_EMAIL,
        "password": "NewPass@999"
    }, timeout=10)
    
    if resp.status_code == 200 and "access_token" in resp.json():
        NEW_ACCESS_TOKEN = resp.json()["access_token"]
        test("7b. Login with new password -> 200", True, resp.status_code, "Got new access_token")
    else:
        test("7b. Login with new password -> 200", False, resp.status_code, f"Response: {resp.text[:200]}")
        NEW_ACCESS_TOKEN = None
except Exception as e:
    test("7b. Login with new password -> 200", False, details=f"Exception: {e}")
    NEW_ACCESS_TOKEN = None

# 7c. Login with old password -> 401
try:
    resp = requests.post(f"{BASE_URL}/admin/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }, timeout=10)
    test("7c. Login with old password -> 401", resp.status_code == 401, resp.status_code)
except Exception as e:
    test("7c. Login with old password -> 401", False, details=f"Exception: {e}")

# 7d. Change password back to original
if NEW_ACCESS_TOKEN:
    try:
        resp = requests.post(f"{BASE_URL}/admin/change-password",
            headers={"Authorization": f"Bearer {NEW_ACCESS_TOKEN}"},
            json={
                "current_password": "NewPass@999",
                "new_password": ADMIN_PASSWORD
            }, timeout=10)
        test("7d. Change password back to original -> 200", resp.status_code == 200, resp.status_code, f"Response: {resp.text[:100]}")
    except Exception as e:
        test("7d. Change password back to original -> 200", False, details=f"Exception: {e}")
else:
    test("7d. Change password back to original -> 200", False, details="Skipped - no new access token")

# 7e. Verify original password works again
try:
    resp = requests.post(f"{BASE_URL}/admin/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    }, timeout=10)
    test("7e. Login with restored password -> 200", resp.status_code == 200, resp.status_code)
except Exception as e:
    test("7e. Login with restored password -> 200", False, details=f"Exception: {e}")

# ============================================================================
# Print Summary
# ============================================================================
print_summary()

# Exit with appropriate code
failed = sum(1 for p, _ in results if not p)
sys.exit(0 if failed == 0 else 1)
