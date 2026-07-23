#!/usr/bin/env python3
"""
Script to check links in course catalog data specifically for:
- linkToLocalWebsiteOrCatalogue: Links to university websites or course catalogues
- LMS: Links to Learning Management Systems (e.g., Moodle)
"""

import json
import sys
import time  # for sleeping

# import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import certifi
import dotenv
import urllib3

# warnings.filterwarnings("ignore", category=DeprecationWarning, module="urllib3")

NUMBER_PARALLEL_REQUESTS = 2  # also the number of parallel requests

# Load environment variables from .env file
dotenv.load_dotenv()


class CourseLinkChecker:
    """Check course links including university catalogues and LMS."""

    def __init__(self):
        self.session = self._create_session()
        self.stats = {"total": 0, "successful": 0, "failed": 0}
        self.url_details = []  # This will store links to be checked
        self.results = []  # This will store the check results

    def _get_credentials_for_university(self, university_name: str) -> Optional[Dict]:
        """Get credentials for a specific university from environment variables.

        Environment variable format (loaded from .env):
        - CC_USER_{UNIVERSITY}: Username for LMS
        - CC_PW_{UNIVERSITY}: Password for LMS

        Example: CC_USER_UG=your_username, CC_PW_UG=your_password
        """
        username_key = f"CC_USER_{university_name}"
        password_key = f"CC_PW_{university_name}"

        username = dotenv.get_key(".env", username_key) if Path(".env").exists() else None
        password = dotenv.get_key(".env", password_key) if Path(".env").exists() else None

        print(f"username = {username}")
        print(f"password = {password}")

        if username and password:
            return {"username": username, "password": password}
        return None

    def _create_session(self) -> urllib3.PoolManager:
        """Create a session with retry logic and common headers."""
        return urllib3.PoolManager(
            timeout=urllib3.Timeout(connect=1.0, read=2.0),
            retries=urllib3.Retry(1, redirect=2),
            cert_reqs="CERT_REQUIRED",
            ca_certs=certifi.where(),
            num_pools=11,  # for 11 unis
            maxsize=NUMBER_PARALLEL_REQUESTS,  # for parallel requests to same host
        )

    def _is_protected_url(self, url: str) -> Dict[str, str | bool]:
        """Check if URL requires authentication and determine university."""
        url_lower = url.lower()

        # TODO find the other linked servers and set defaults

        # Check for Moodle instances
        if "moodle.uni-greifswald.de" in url_lower:
            return {
                "is_protected": True,
                "type": "LMS",
                "base_url": "https://moodle.uni-greifswald.de",
                "login_path": "/login/index.php",
                "university": "UG",
                "shibboleth": "https://idp.uni-greifswald.de/idp/profile/SAML2/Redirect/SSO?execution=e1s2",
            }
        if "moodle.buas" in url_lower:
            return {
                "is_protected": True,
                "type": "LMS",
                "base_url": "https://moodle.buas.nl",
                "login_path": "/login/index.php",
                "university": "BUas",
            }
        if "moodle" in url_lower:
            # Generic Moodle detection - extract base domain
            from urllib.parse import urlparse

            parsed = urlparse(url)
            if parsed.netloc == "moodle" or "moodle" in parsed.path:
                return {
                    "is_protected": True,
                    "type": "LMS",
                    "base_url": f"https://{parsed.netloc}",
                    "login_path": "/login/index.php",
                    "university": parsed.netloc.replace("moodle.", "").split(".")[0].upper(),
                }

        # Check for IPT
        if "ipt.pt" in url_lower or "portal2.ipt.pt" in url_lower:
            return {
                "is_protected": True,
                "type": "ipt",
                "base_url": "https://portal2.ipt.pt",
                "login_path": "/login.php",
                "university": "IPT",
            }

        return {"is_protected": False}

    def _check_login_required(self, url: str) -> bool:
        """Check if URL requires authentication."""
        try:
            response = self.session.request("GET", url, timeout=3)

            status_codes_with_login = [301, 302, 303, 307, 308]
            login_patterns = ["login/index.php", "login.php", "idp/"]

            return (
                response.status in status_codes_with_login
                and (
                    "login" in response.headers.get("Location", "").lower()
                    or "auth" in response.headers.get("Location", "").lower()
                    or any(pattern in str(response.url or "").lower() for pattern in login_patterns)
                )
            ) or ("moodle" in url.lower() and response.status == 400)
        except urllib3.exceptions.TimeoutError:
            return False
        except urllib3.exceptions.RequestError:
            return False

    def _login_to_LMS(
        self, base_url: str, login_path: str, protected_info: Dict, credentials: Dict
    ) -> bool:
        """Log in to LMS using credentials. Supports both standard Moodle login and Shibboleth SSO."""
        login_url = f"{base_url}{login_path}"

        # Step 1: GET the login page to establish cookies and session tokens
        self.session.request("GET", login_url)

        # TODO logins for the other unis

        # Step 2: Handle Shibboleth SSO for University of Greifswald
        if "greifswald" in base_url and "shibboleth" in protected_info:
            return self._login_via_shibboleth(protected_info, credentials)

        # Step 3: Standard Moodle login
        return self._login_to_moodle(login_url, credentials)

    def _login_via_shibboleth(self, protected_info: Dict, credentials: Dict) -> bool:
        """Handle Shibboleth SSO login flow for University of Greifswald.

        Flow:
        1. GET the Shibboleth SSO endpoint -> redirects to IdP
        2. GET the IdP login page -> gets the login form with hidden fields
        3. POST credentials to the IdP login endpoint -> validates and redirects back
        4. Follow all redirects back to Moodle
        """
        # Step 1: GET the Shibboleth SSO endpoint to get the redirect to IdP
        sso_url = protected_info["shibboleth"]
        response = self.session.request("GET", sso_url, allow_redirects=False)

        if response.status not in (301, 302, 303, 307, 308):
            # Maybe already authenticated or error
            return response.status < 400

        # Step 2: Follow redirect to the IdP login page
        redirect_url = response.headers.get("Location", "")
        if not redirect_url:
            return False

        if not redirect_url.startswith("http"):
            redirect_url = (
                f"https://{redirect_url}"
                if not redirect_url.startswith("/")
                else f"https://idp.uni-greifswald.de{redirect_url}"
            )

        idp_response = self.session.request("GET", redirect_url)

        # Step 3: Extract the IdP login form action URL and hidden fields from the response body
        idp_body = (
            idp_response.data.decode("utf-8", errors="replace")
            if isinstance(idp_response.data, bytes)
            else str(idp_response.data)
        )

        # Parse hidden form fields from the IdP login page
        hidden_fields = {}
        import re

        for match in re.finditer(r'name="([^"]+)"\s+value="([^"]*)"', idp_body):
            hidden_fields[match.group(1)] = match.group(2)

        # Step 4: POST credentials to the IdP login endpoint
        # Extract the form action from the page
        form_action_match = re.search(r'action="([^"]*)"', idp_body)
        if form_action_match:
            form_action = form_action_match.group(1)
            if not form_action.startswith("http"):
                form_action = "https://idp.uni-greifswald.de" + form_action
        else:
            form_action = redirect_url

        # Build the login data with hidden fields + credentials
        login_data = dict(hidden_fields)
        login_data["username"] = credentials.get("username", "")
        login_data["password"] = credentials.get("password", "")

        auth_response = self.session.request(
            "POST",
            form_action,
            fields=login_data,
        )

        return auth_response.status < 400

    def _login_to_moodle(self, login_url: str, credentials: Dict) -> bool:
        """Handle standard Moodle login flow."""
        response = self.session.request(
            "POST",
            login_url,
            fields={
                "username": credentials.get("username", ""),
                "password": credentials.get("password", ""),
                "rememberusername": "1",
            },
        )

        return response.status < 400

    def _login_to_url(self, url: str) -> bool:
        """Attempt to log in to protected URL using university-specific credentials."""

        protected_info = self._is_protected_url(url)
        if not protected_info["is_protected"] or "university" not in protected_info:
            return False

        # Get credentials specific to this university (university string is guaranteed)
        university_name = str(protected_info["university"])
        university_credentials = self._get_credentials_for_university(university_name)

        if not university_credentials:
            return False

        try:
            if protected_info["type"] == "LMS":
                base_url = protected_info["base_url"]
                login_path = protected_info["login_path"]
                if isinstance(base_url, str) and isinstance(login_path, str):
                    return self._login_to_LMS(
                        base_url, login_path, protected_info, university_credentials
                    )

            return False
        except Exception as e:
            print(f"Login attempt failed for {protected_info['university']}: {e}")
            return False

    def _check_url(self, url: str) -> Tuple[bool, str]:
        """Check URL accessibility with optional login."""

        try:
            # Initial GET request with timeout
            response = self.session.request("GET", url, timeout=3)

            if response.status < 400:
                return True, f"HTTP {response.status}"

            # Check if this is a Moodle course page - these might need authentication
            if "moodle" in url.lower():
                # Moodle course pages typically need enrollment
                # Try to access with authentication
                if self._is_protected_url(url)["is_protected"]:
                    if self._login_to_url(url):
                        response = self.session.request(
                            "GET",
                            url,
                            timeout=3,
                        )
                        if response.status < 400:
                            return True, f"HTTP {response.status} (logged in)"
                        return False, f"HTTP {response.status} (logged in)"
                    return False, "login failed"

            # Try login if URL requires authentication
            if self._check_login_required(url):
                if self._login_to_url(url):
                    response = self.session.request(
                        "GET",
                        url,
                        timeout=3,
                    )
                    if response.status < 400:
                        return True, f"HTTP {response.status} (logged in)"
                    return False, f"HTTP {response.status} (logged in)"
                return False, f"HTTP {response.status} (login failed)"

        except urllib3.exceptions.TimeoutError:
            return False, "Timeout"
        except urllib3.exceptions.RequestError as e:
            return False, f"Request failed: {str(e)}"

        return False, f"HTTP {getattr(response, 'status', 'unknown')}"

    def _extract_course_links(self, file_path: Path, source) -> List[Dict[str, object]]:
        """Extract course links from JSON data."""
        links_found = []
        title = str(source.get("courseName", "Unknown"))
        seen_urls = set()  # Track URLs we've already added to avoid duplicates

        for field in ["linkToLocalWebsiteOrCatalogue", "LMS"]:
            for link in source.get(field, []):
                if isinstance(link, str) and link and link not in seen_urls:
                    seen_urls.add(link)
                    links_found.append(
                        {"course": title, "file": file_path.name, "field": field, "url": link}
                    )

        return links_found

    def _extract_course_links_from_json_file(self, file_path: Path) -> List[Dict[str, object]]:
        """Extract course links from a JSON file."""
        try:
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                data = json.load(f)
                courses = [data] if isinstance(data, dict) else data

                for course in courses:
                    if isinstance(course, dict):
                        self.url_details.extend(self._extract_course_links(file_path, course))
        except json.JSONDecodeError as e:
            print(f"Warning: Could not parse JSON in {file_path}: {e}")
        except Exception as e:
            print(f"Warning: Error reading {file_path}: {e}")

        return self.url_details

    def process_file(self, file_path: Path) -> None:
        """Process a single JSON file."""
        print(f"Processing: {file_path}")
        print("-" * 80)
        self._extract_course_links_from_json_file(file_path)
        print(f"Found {len(self.url_details)} links in {file_path.name}")

    def check_urls(self, links: List[Dict[str, object]]) -> None:
        """Check URL accessibility in parallel."""
        print("Checking course links...")
        print("-" * 80)

        with ThreadPoolExecutor(max_workers=NUMBER_PARALLEL_REQUESTS) as executor:
            futures = {executor.submit(self._check_url, str(item["url"])): item for item in links}

            for i, future in enumerate(as_completed(futures), 1):
                item = futures[future]
                self.stats["total"] += 1

                try:
                    is_accessible, message = future.result()

                    if is_accessible:
                        self.stats["successful"] += 1
                        status = "✓"
                    else:
                        self.stats["failed"] += 1
                        status = "✗"

                    result = {
                        "course": item["course"],
                        "file": item["file"],
                        "field": item["field"],
                        "url": item["url"],
                        "accessible": is_accessible,
                        "status": message,
                    }
                    self.results.append(result)

                    print(f"[{i}/{self.stats['total']}] {status} {item['course']}")
                    print(f"         {item['field']}: {item['url']}")
                    print(f"         Status: {message}")

                    # TODO really necessary? - talk to Thomas
                    if i < len(links):
                        time.sleep(0.1)

                except Exception as e:
                    self.stats["failed"] += 1
                    error_message = f"Exception: {str(e)}"
                    print(f"[{i}/{self.stats['total']}] ✗ {item['course']} - {error_message}")

                    result = {
                        "course": item["course"],
                        "file": item["file"],
                        "field": item["field"],
                        "url": item["url"],
                        "accessible": False,
                        "status": error_message,
                    }
                    self.results.append(result)

    def print_summary(self) -> None:
        """Print summary statistics and findings."""
        if self.stats["total"] == 0:
            return

        print()
        print()
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"Total links checked: {self.stats['total']}")
        print(
            f"Accessible: {self.stats['successful']} ({self.stats['successful']/self.stats['total']*100:.1f}%)"
        )
        print(
            f"Inaccessible: {self.stats['failed']} ({self.stats['failed']/self.stats['total']*100:.1f}%)"
        )
        print()

        # Group by field
        for field in ["linkToLocalWebsiteOrCatalogue", "LMS"]:
            print("=" * 80)
            print(f"INACCESSIBLE {field.replace('-', ' ')} LINKS")
            print("=" * 80)

            field_links = [
                result
                for result in self.results
                if not result["accessible"] and result["field"] == field
            ]

            if field_links:
                for result in field_links:
                    print(f"✗ {result['course']}")
                    print(f"  File: {result['file']}")
                    print(f"  URL: {result['url']}")
                    print(f"  Reason: {result['status']}")
                    print()
            else:
                print(f"All {field} links are accessible!")
                print()

    def save_report(self) -> Path:
        """Save detailed report to JSON file."""
        report_file = Path.cwd() / "course_links_report.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump(
                {"stats": self.stats, "results": self.results}, f, indent=2, ensure_ascii=False
            )
        return report_file


def main():
    """Main function to run the script."""
    if len(sys.argv) < 2:
        print("Usage: python check_course_links.py <file_path>")
        print("Example: python check_course_links.py data/course.json")
        return

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"Error: File or directory '{sys.argv[1]}' does not exist.")
        return

    print("=" * 80)
    print("Checking Course Link Fields")
    print("=" * 80)

    checker = CourseLinkChecker()
    checker.process_file(file_path)

    if not checker.url_details:
        print("No course links found to check.")
        return

    checker.check_urls(checker.url_details)
    checker.print_summary()
    report_file = checker.save_report()

    print("=" * 80)
    print(f"Full detailed report saved to: {report_file}")
    print("=" * 80)


if __name__ == "__main__":
    main()
